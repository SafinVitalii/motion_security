import datetime
import time

import cv2
import imutils
import numpy as np
from imutils.video import VideoStream

from processors.basicmotiondetector import BasicMotionDetector
from processors.buffer import Buffer


def get_optimal_fps():
    video = cv2.VideoCapture(0)
    num_frames = 240  # Number of frames to capture

    print "Capturing {0} frames".format(num_frames)

    start = time.time()  # Start time

    # Grab a few frames
    for i in xrange(0, num_frames):
        ret, frame = video.read()

    end = time.time()  # End time

    seconds = end - start  # Time elapsed
    print "Time taken : {0} seconds".format(seconds)

    # Calculate frames per second
    fps = num_frames / seconds
    print "Estimated frames per second : {0}".format(fps)


def capture_video_one_fps(seconds):
    cap = cv2.VideoCapture(0)

    buffer = []
    end = time.time() + seconds
    while time.time() < end:
        ret, frame = cap.read()
        if ret:
            buffer.append(frame)
        else:
            break
        time.sleep(0.95)

    # Release everything if job is finished
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(
        '/home/vitalii/PycharmProjects/rasp-security/videos/output.avi',
        fourcc, 1, (640, 480)
    )
    for frame in buffer:
        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()


def capture_video_and_motion():
    webcam = VideoStream(src=0).start()
    cam_motion = BasicMotionDetector()
    total = 0
    camera_fps = 9.5
    sleep_after_frame = 1 / camera_fps
    buffer = Buffer()
    frames = []

    while True:
        time.sleep(sleep_after_frame)

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

        if len(locs) > 0:
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
            cv2.imshow("Camera", frame)
        buffer.append(frame)
        frames = []

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    # Cleanup
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(
        '/home/vitalii/PycharmProjects/rasp-security/videos/output.avi',
        fourcc, camera_fps, (400, 300)
    )
    for frame in buffer:
        out.write(frame)
    cv2.destroyAllWindows()
    webcam.stop()


if __name__ == '__main__':
    # capture_video_one_fps(5)
    # get_optimal_fps()
    capture_video_and_motion()
