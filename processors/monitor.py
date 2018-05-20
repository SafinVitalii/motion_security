import datetime
import os
import time
import threading

import cv2
import imutils
import numpy as np
from imutils.video import VideoStream

from app.info import available_devices
from processors.basicmotiondetector import BasicMotionDetector
from processors.buffer import Buffer
from processors.mailer import Mailer

STATUS_AVAILABLE = 1
STATUS_PROVISIONING = 2
STATUS_LIVE = 3
STATUS_MAPPINGS = {
    STATUS_AVAILABLE: "Available",
    STATUS_PROVISIONING: "Provisioning",
    STATUS_LIVE: "Live"
}
CAMERA_PROPS = ['CV_CAP_PROP_POS_MSEC', 'CV_CAP_PROP_FPS',
                'CV_CAP_PROP_CONTRAST', 'CV_CAP_PROP_POS_FRAMES', 'CV_CAP_PROP_HUE',
                'CV_CAP_PROP_WHITE_BALANCE', 'CV_CAP_PROP_RECTIFICATION',
                'CV_CAP_PROP_POS_AVI_RATIO', 'CV_CAP_PROP_MODE',
                'CV_CAP_PROP_BRIGHTNESS', 'CV_CAP_PROP_FORMAT', 'CV_CAP_PROP_CONVERT_RGB',
                'CV_CAP_PROP_GAIN', 'CV_CAP_PROP_SATURATION', 'CV_CAP_PROP_FOURCC']


class MonitorContainer(object):
    def __init__(self):
        self.d = []

    def setup_monitors(self):
        devices = available_devices()
        for i in range(0, len(devices)):
            self.d.append(Monitor(webcam_id=i))

    def sync_monitors(self):
        pass

    def available_devices(self):
        self.sync_monitors()
        resp = []
        for mon in self.d:
            resp.append({str(mon.webcam_id): STATUS_MAPPINGS.get(mon.status)})
        return resp

    def is_monitor_available(self, mon_id):
        if mon_id > len(self.d) or self.d[mon_id].status != STATUS_AVAILABLE:
            return False
        return True

    def is_monitor_provisioning(self, mon_id):
        if mon_id > len(self.d) or self.d[mon_id].status != STATUS_PROVISIONING:
            return False
        return True

    def is_monitor_live(self, mon_id):
        if mon_id > len(self.d) or self.d[mon_id].status != STATUS_LIVE:
            return False
        return True


class Monitor(object):
    def __init__(self, webcam_id, subscribers=None, streaming=False):
        self.mailer = Mailer()
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.webcam_id = webcam_id
        self.out_file = 'output{}.avi'.format(self.webcam_id)
        self.streamer = None
        self.status = STATUS_AVAILABLE
        if not streaming:
            self.camera_fps = 25
            # self.camera_fps = self.get_optimal_fps()
            self.sleep_after_frame = 1 / self.camera_fps
            self.default_buffer_duration = 10
        if not subscribers or not isinstance(subscribers, list):
            subscribers = ["vitaliylviv3@gmail.com"]
        self.subscribers = subscribers

    def start(self):
        t = threading.Thread(target=self._start())
        t.setDaemon(True)
        t.start()

    def _start(self):
        """ Automatic motion capturing """
        webcam = VideoStream(src=self.webcam_id).start()
        cam_motion = BasicMotionDetector()
        total = 0
        buffer = Buffer()
        frames = []
        motions_in_previous = False
        merged_buffers = 1
        frame_limit = self.camera_fps * self.default_buffer_duration

        while self.status == STATUS_PROVISIONING:
            time.sleep(self.sleep_after_frame)

            frame = webcam.read()
            frame = imutils.resize(frame, width=400)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            locs = cam_motion.update(gray)

            # we should allow the motion detector to "run" for a bit
            # and accumulate a set of frames to form a nice average
            starting_frames = 10
            if total < starting_frames:
                total += 1
                frames.append(frame)
                continue

            if locs and total >= starting_frames * 2:
                minX, minY = np.inf, np.inf
                maxX, maxY = -np.inf, -np.inf

                # loop over the locations of motion and accumulate the
                # minimum and maximum locations of the bounding boxes
                for l in locs:
                    (x, y, w, h) = cv2.boundingRect(l)
                    (minX, maxX) = (min(minX, x), max(maxX, x + w))
                    (minY, maxY) = (min(minY, y), max(maxY, y + h))

                cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 0, 255), 2)
                buffer.motions = True
                motions_in_previous = True

            frames.append(frame)
            total += 1
            timestamp = datetime.datetime.now()
            ts = str(timestamp.strftime("%x %X").decode('ascii'))

            for frame in frames:
                cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.35, (0, 0, 255), 1)
                # Uncomment to see picture on the screen
                # cv2.imshow("Camera {}".format(self.webcam_id), frame)
            buffer.append(frame)
            frames = []

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            if not buffer.motions \
                    and motions_in_previous \
                    and len(buffer) >= frame_limit * merged_buffers\
                    or merged_buffers == 10:
                out = cv2.VideoWriter(
                    os.path.join(os.getcwd(), self.out_file),
                    self.fourcc, self.camera_fps, (400, 300)
                )
                for frame in buffer:
                    out.write(frame)
                print "Clearing buffer of {} frames.".format(len(buffer))
                del buffer[:]
                motions_in_previous = False
                merged_buffers = 1
                date = datetime.datetime.now().strftime("%x")
                self.mailer.send_mail(
                    send_from="mailtestrasp@gmail.com",
                    send_to=self.subscribers,
                    subject="Raspberry Pi monitoring alert {}".format(date),
                    text="Hi! Look what happened during your absence.",
                    files=[os.path.join(os.getcwd(), self.out_file)]
                )
                print "Report was sent to : {}".format(','.join(self.subscribers[0:5]))
                if len(self.subscribers) > 5:
                    print "And a few others. Total mails sent: {}".format(len(self.subscribers))

            elif len(buffer) >= frame_limit * merged_buffers:
                if buffer.motions:
                    print "Continue with recording. Current buffer size: {} seconds".format(
                        len(buffer) / self.camera_fps
                    )
                    merged_buffers += 1
                else:
                    print "Dropping buffer of {} frames.".format(len(buffer))
                    del buffer[:]
                buffer.motions = False

        # Cleanup
        cv2.destroyAllWindows()
        webcam.stop()

    def get_frame(self):
        """ Read frame and encode to jpg"""
        success, image = self.streamer.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def stream(self):
        """Video streaming generator function."""
        if not self.streamer:
            self.streamer = cv2.VideoCapture(self.webcam_id)
        while True:
            frame = self.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    def __del__(self):
        self.streamer.release()

    def get_optimal_fps(self):
        """ Get average FPS for the camera """
        if not self.streamer:
            self.streamer = cv2.VideoCapture(self.webcam_id)
        video = self.streamer
        num_frames = 250  # Number of frames to capture

        print "Capturing {} frames".format(num_frames)

        start = time.time()
        for i in xrange(0, num_frames):
            video.read()
        end = time.time()
        seconds = end - start  # Time elapsed
        print "Time taken : {} seconds".format(seconds)

        fps = num_frames / seconds
        self.camera_fps = fps
        print "Estimated frames per second : {}".format(fps)

        self.streamer.release()
        return self.camera_fps

    def get_config(self):
        if not self.streamer:
            self.streamer = cv2.VideoCapture(self.webcam_id)
        props = {}
        for idx, prop in enumerate(CAMERA_PROPS):
            props[prop.replace('CV_CAP_PROP_', '').replace('_', ' ').capitalize()] = \
                self.streamer.get(idx)

        self.streamer.release()
        return props

    def set_status(self, status):
        if status not in (1, 2, 3) or self.status == status:
            return False
        self.status = status
        return True
