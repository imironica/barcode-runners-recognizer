import numpy as np
import cv2
import warnings

warnings.filterwarnings("ignore")

# Detect the location of barcodes from a image
class BarcodeDetector(object):

    def __init__(self, useDebugMode=False):
        self.useDebugMode = useDebugMode

    def cropMinAreaRect(self, img, rect):
        rows, cols, ch = img.shape
        rectDev = [(rect[0][0]), (rect[1][0]), (rect[2][0]), (rect[3][0])]
        rectNew = self.getPointsInOrder2(rectDev)

        # rotate img
        size = rectNew[1][0] - rectNew[0][0]

        pts1 = np.float32([rectNew[0], rectNew[1], rectNew[2]])
        pts2 = np.float32([[0, 0], [size, 0], [size, size]])
        M = cv2.getAffineTransform(pts1, pts2)
        dst = cv2.warpAffine(img, M, (cols, rows))

        img_crop = dst[0:size, 0:size]
        return img_crop

    def getPointsInOrder(self, points):
        args = []
        for i in range(0, 4):
            args.append(points[i, 0] * points[i, 0] + points[i, 1] * points[i, 1])
        indexes = sorted(range(len(args)), key=lambda k: args[k])

        point1 = points[indexes[0], :]
        point3 = points[indexes[3], :]

        pointCandidate1 = points[indexes[1], :]
        pointCandidate2 = points[indexes[2], :]

        if pointCandidate1[0] > pointCandidate2[0] and pointCandidate1[1] < pointCandidate2[1]:
            point2 = pointCandidate1
            point4 = pointCandidate2
        else:
            point2 = pointCandidate2
            point4 = pointCandidate1

        return [point1, point2, point3, point4]

    def getPointsInOrder2(self, points):
        args = []
        for i in range(0, 4):
            args.append(points[i][0] * points[i][0] + points[i][1] * points[i][1])
        indexes = sorted(range(len(args)), key=lambda k: args[k])

        point1 = points[indexes[0]]
        point3 = points[indexes[3]]

        pointCandidate1 = points[indexes[1]]
        pointCandidate2 = points[indexes[2]]

        if pointCandidate1[0] > pointCandidate2[0] and pointCandidate1[1] < pointCandidate2[1]:
            point2 = pointCandidate1
            point4 = pointCandidate2
        else:
            point2 = pointCandidate2
            point4 = pointCandidate1

        return [point1, point2, point3, point4]


    def isBarecodeCandidate(self, points, image, rect):

        thresh = 50
        threshLength = 20
        threshLengthMax = 250
        thresholdRatioMin = 0.8
        thresholdRatioMax = 1.2
        cropImage = None

        points = self.getPointsInOrder(points)

        point1 = points[0]
        point2 = points[1]
        point3 = points[2]
        point4 = points[3]

        # verify that the boundaries of the image are between the image
        if point1[0] < 0 or point1[1] < 0:
            return 0, cropImage

        if point3[0] > image.shape[1] or point3[1] > image.shape[0]:
            return 0, cropImage

        # verify the angle  (it should be a rectangle)
        if abs(point1[1] - point2[1]) > thresh or abs(point2[0] - point3[0]) > thresh or abs(
                point3[1] - point4[1]) > thresh or abs(point4[0] - point1[0]) > thresh:
            return 0, cropImage
        # return 1

        # verify that each segment is bigger than a threshold
        # if size is lower we will not be able to recognize the code
        if abs(point1[0] - point2[0]) < threshLength or abs(point3[0] - point4[0]) < threshLength:
            return 0, cropImage
        # return 1

        # verify that each segment is bigger than a threshold
        # if size is lower we will not be able to recognize the code
        if abs(point1[1] - point4[1]) < threshLength or abs(point2[1] - point3[1]) < threshLength:
            return 0, cropImage
        # return 1

        # verify that a side of a square is not bigger than threshLengthMax
        # (the square cannot be very big)
        if abs(point1[0] - point2[0]) > threshLengthMax or abs(point3[0] - point4[0]) > threshLengthMax:
            return 0, cropImage

        # verify that a side of a square is not bigger
        # than threshLengthMax (the square cannot be very big)
        if abs(point1[1] - point4[1]) > threshLengthMax or abs(point2[1] - point3[1]) > threshLengthMax:
            return 0, cropImage

        # verify the ration of the square
        ratio = abs(point1[1] - point4[1]) / abs(point1[0] - point2[0])

        if ratio > thresholdRatioMax or ratio < thresholdRatioMin:
            return 0, cropImage

        cropImage = self.cropMinAreaRect(image, rect)

        return 1, cropImage

    def processImage(self, image_path):

        image = cv2.imread(image_path)

        # equalize the histogram of the Y channel
        img_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        img_lab[:, :, 0] = cv2.equalizeHist(img_lab[:, :, 0])

        # take the grayscale image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # binarize the image
        (ret, thresh) = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY)

        # switch the values of the image: 0->255 / 255->0
        thresh = cv2.bitwise_not(thresh)

        # find the contours in the binarized image, then sort the contours
        # by their area, keeping only the largest one
        im2, cnts, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []

        for currentContour in cnts:

            rect = cv2.minAreaRect(currentContour)
            box = np.int0(cv2.boxPoints(rect))
            perimeter = cv2.arcLength(currentContour, True)
            approx = cv2.approxPolyDP(currentContour, 0.025 * perimeter, True)

            if approx.shape[0] == 4:
                isCandidate, boxRGB = self.isBarecodeCandidate(box, image, approx)
                if isCandidate == 1:

                    if self.useDebugMode:
                        cv2.drawContours(image, [approx], -1, (0, 0, 255), 6)

                    boxes.append(boxRGB)

        return image, boxes
