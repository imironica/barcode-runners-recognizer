# USAGE
# python evaluateAlgorihm.py --image Db/Images/DM_DCM_1759.jpeg

# import the necessary packages
import cv2
import os
from BarcodeDetector import BarcodeDetector
from BarcodeRecognizer import BarcodeRecognizer
import json

images = []
folderTestImages = 'db/Images/'
folderProcessedImages = 'db/Results/'
folderProcessedBoxes = 'db/Barcodes/'

detector = BarcodeDetector(useDebugMode=True)
saveResults = True
filenameImages = [f for f in os.listdir(folderTestImages) if f.endswith('.jpeg')]
filenamesGT = [f for f in os.listdir(folderTestImages) if f.endswith('.json')]


def computeDistanceBarcode(barcode1, barcode2):
    barcodeList1 = [int(k) for k in barcode1]
    barcodeList2 = [int(k) for k in str(barcode2)]
    distance = 0
    for i in range(0, len(barcodeList1)):
        distance = distance + abs(barcodeList1[i] - barcodeList2[i])
    return distance


def findMinimumDistance(barcode, barcodeList):
    found = False
    thresholdDistanceBarcode = 5
    for currentBarcode in barcodeList:
        if computeDistanceBarcode(barcode, currentBarcode) < thresholdDistanceBarcode:
            return True, currentBarcode

    return found, None


# Get the ground truth
gtValues = []
for filenameGT in filenamesGT:
    gt = []
    pathGT = os.path.join(folderTestImages, filenameGT)
    with open(pathGT) as json_data:
        gt = json.load(json_data)
    if gt['Codes'] is not None:
        gtValues = gtValues + gt['Codes']

gtValues = list(set(gtValues))

index = 0
correctFound = 0
total = 0

for filename in filenameImages:
    print('Process filename {0} {1}'.format(str(index), filename))
    pathImage = os.path.join(folderTestImages, filename)

    gt = []
    with open(pathImage + '.json') as json_data:
        gt = json.load(json_data)
    total = total + len(gt['Codes'])
    imageProcessed, boxes = detector.processImage(pathImage)

    foundCodes = []
    recognizer = BarcodeRecognizer()
    idBox = 1
    for box in boxes:
        valid, code = recognizer.reconize(box)
        if valid:
            currentCode = ''
            for digit in code:
                currentCode += str(digit)
            isFoundInDb, currentCode = findMinimumDistance(currentCode, gtValues)
            if isFoundInDb is True:
                foundCodes.append(currentCode)
                pathImageBoxName = "{}{}_{}.jpg".format(folderProcessedBoxes, filename, idBox)
                cv2.imwrite(pathImageBoxName, box)
                idBox = idBox + 1
    found = 0
    for code in gt['Codes']:
        if code in foundCodes:
            found = found + 1

    correctFound = correctFound + found

    if saveResults:
        if len(gt['Codes']) == found:
            pathImageProcessed = os.path.join(folderProcessedImages, 'OK', filename)
        else:
            pathImageProcessed = os.path.join(folderProcessedImages, 'NOTOK', filename)
        height, width = imageProcessed.shape[:2]
        res = cv2.resize(imageProcessed, (int(width / 8), int(height / 8)))
        cv2.imwrite(pathImageProcessed, res)

    index = index + 1
    print('Detected {0} from {1}'.format(found, len(gt['Codes'])))

print('Final result: {0} correct detected from {1} '.format(correctFound, total))
