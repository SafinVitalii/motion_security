# import the necessary packages
import cv2


class BasicMotionDetector:
    def __init__(self, accumWeight=0.5, deltaThresh=5, minArea=5000):
        self.isv2 = False
        self.deltaThresh = deltaThresh
        self.accumWeight = accumWeight
        self.minArea = minArea
        self.avg = None

    def update(self, image):
        locs = []

        if self.avg is None:
            self.avg = image.astype("float")
            return locs

        cv2.accumulateWeighted(image, self.avg, self.accumWeight)
        frame_delta = cv2.absdiff(image, cv2.convertScaleAbs(self.avg))

        thresh = cv2.threshold(frame_delta, self.deltaThresh, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if self.isv2 else cnts[1]

        for c in cnts:
            if cv2.contourArea(c) > self.minArea:
                locs.append(c)

        return locs
