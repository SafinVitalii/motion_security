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

        # otherwise, accumulate the weighted average between
        # the current frame and the previous frames, then compute
        # the pixel-wise differences between the current frame
        # and running average
        cv2.accumulateWeighted(image, self.avg, self.accumWeight)
        frameDelta = cv2.absdiff(image, cv2.convertScaleAbs(self.avg))

        # threshold the delta image and apply a series of dilations
        # to help fill in holes
        thresh = cv2.threshold(frameDelta, self.deltaThresh, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # find contours in the thresholded image, taking care to
        # use the appropriate version of OpenCV
        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if self.isv2 else cnts[1]

        # loop over the contours
        for c in cnts:
            # only add the contour to the locations list if it
            # exceeds the minimum area
            if cv2.contourArea(c) > self.minArea:
                locs.append(c)

        # return the set of locations
        return locs
