import datetime
import os
import time

import cv2
import imutils
import numpy as np
from imutils.video import VideoStream

from processors.basicmotiondetector import BasicMotionDetector
from processors.buffer import Buffer
from processors.mailer import Mailer


class Monitor(object):
    def __init__(self, webcam_id, subscribers=None):
        self.mailer = Mailer()
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.webcam_id = webcam_id
        self.out_file = 'output{}.avi'.format(self.webcam_id)
        self.camera_fps = self.get_optimal_fps()
        self.sleep_after_frame = 1 / self.camera_fps
        self.default_buffer_duration = 10
        self.optimal_fps = None
        if not subscribers or not isinstance(subscribers, list):
            subscribers = ["vitaliylviv3@gmail.com"]
        self.subscribers = subscribers

    def capture_video_and_motion(self):
        webcam = VideoStream(src=self.webcam_id).start()
        cam_motion = BasicMotionDetector()
        total = 0
        buffer = Buffer()
        frames = []

        while True:
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

            if locs:
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

            frames.append(frame)
            total += 1
            timestamp = datetime.datetime.now()
            ts = str(timestamp.strftime("%x %X").decode('ascii'))

            for frame in frames:
                cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.35, (0, 0, 255), 1)
                cv2.imshow("Camera {}".format(self.webcam_id), frame)
            buffer.append(frame)
            frames = []

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            if buffer.motions and len(buffer) >= self.camera_fps * self.default_buffer_duration:
                out = cv2.VideoWriter(
                    os.path.join(os.getcwd(), self.out_file),
                    self.fourcc, self.camera_fps, (400, 300)
                )
                for frame in buffer:
                    out.write(frame)
                print "Clearing buffer of {} frames.".format(len(buffer))
                del buffer[:]
                buffer.motions = False
                date = datetime.datetime.now().strftime("%x")
                self.mailer.send_mail(
                    send_from="mailtestrasp@gmail.com",
                    send_to=self.subscribers,
                    subject="Raspberry Pi monitoring alert {}".format(date),
                    text="Hi! Look what happened during your absence.",
                    files=[os.path.join(os.getcwd(), self.out_file)]
                )
                print "Report was sent."

            elif len(buffer) >= self.camera_fps * self.default_buffer_duration:
                print "Dropping buffer of {} frames.".format(len(buffer))
                del buffer[:]
                buffer.motions = False

        # Cleanup
        cv2.destroyAllWindows()
        webcam.stop()

    def get_optimal_fps(self):
        """ Get average FPS for the camera """
        video = cv2.VideoCapture(self.webcam_id)
        num_frames = 250  # Number of frames to capture

        print "Capturing {} frames".format(num_frames)

        start = time.time()
        for i in xrange(0, num_frames):
            video.read()
        end = time.time()
        seconds = end - start  # Time elapsed
        print "Time taken : {} seconds".format(seconds)

        fps = num_frames / seconds
        self.optimal_fps = fps
        print "Estimated frames per second : {}".format(fps)

        return self.optimal_fps
