import numpy as np
import cv2

# Recognize the code from a barcode location
class BarcodeRecognizer(object):

    def __init__(self, useDebugMode=False):
        self.useDebugMode = useDebugMode

    def reconize(self, image):
        if image is None:
            return False, None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if gray is None:
            return False, None

        gray = cv2.resize(gray, (100, 100), interpolation=cv2.INTER_CUBIC)
        valid = True
        marginSize = 5
        kernel = np.ones((7, 7), np.uint8)

        # binarize the image
        (ret, thresh) = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)

        width, height = thresh.shape
        thresh[0:marginSize, 0:height] = 0
        thresh[width - marginSize:width, 0:height] = 0
        thresh[0:width, 0:marginSize] = 0
        thresh[0:width, height - marginSize:height] = 0

        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # find first corner
        found = False
        index = 0
        leftCorner = 0

        while found is False and index < width:
            if thresh[index, index] == 255:
                leftCorner = index
                found = True
            index = index + 1

        index = 0
        found = False
        rightCorner = 0

        while found is False and index < width:
            if thresh[index, height - index - 1] == 255:
                rightCorner = index
                found = True
            index = index + 1

        index = 0
        found = False
        buttomCorner = 0

        while found is False and index < width:
            if thresh[width - index - 1, index] == 255:
                buttomCorner = index
                found = True
            index = index + 1

        index = 0
        lastCorner = 0

        found = False
        while found is False and index < width:
            if thresh[width - index - 1, height - index - 1] == 255:
                lastCorner = index
                found = True
            index = index + 1

        if lastCorner < leftCorner \
                or lastCorner < rightCorner \
                or lastCorner < buttomCorner:
            valid = False
            return valid, None

        pts1 = np.float32([[leftCorner, leftCorner],
                           [rightCorner, height - rightCorner - 1],
                           [width - buttomCorner - 1, buttomCorner]])

        pts2 = np.float32([[0, 0], [0, 100], [100, 0]])
        affineTransform = cv2.getAffineTransform(pts1, pts2)
        thresh = cv2.warpAffine(thresh, affineTransform, (width, height))
        (ret, threshCentrated) = cv2.threshold(thresh, 125, 255, cv2.THRESH_BINARY)

        valuesPredicted = np.zeros(25, np.int8)

        index = 0
        threshRecValue = 18 * 255

        for i in range(0, 5):
            for j in range(0, 5):
                cv2.rectangle(threshCentrated, (i * 20, j * 20), (i * 20 + 20, j * 20 + 20), 128, 1)
                sum = threshCentrated[i * 20 + 7:i * 20 + 13, j * 20 + 7:j * 20 + 13].sum().sum()

                if sum > threshRecValue:
                    valuesPredicted[index] = 1
                else:
                    valuesPredicted[index] = 0
                index = index + 1

        valuesPredicted[0] = valuesPredicted[4] = valuesPredicted[20] = 1
        valuesPredicted[24] = 0

        return valid, valuesPredicted
