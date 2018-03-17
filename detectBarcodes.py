# USAGE
# python detectBarcodes.py --image Db/Images/DM_DCM_1759.jpeg

# import the necessary packages
from BarcodeDetector import BarcodeDetector
from BarcodeRecognizer import BarcodeRecognizer
import argparse

ap = argparse.ArgumentParser()

ap.add_argument("-v", "--image", type=str, default="",
                help="path to input image file")
args = vars(ap.parse_args())

filename = args["image"]

detector = BarcodeDetector(useDebugMode=True)
imageProcessed, boxes = detector.processImage(filename)
recognizer = BarcodeRecognizer()
for box in boxes:
    valid, code = recognizer.reconize(box)
    if valid:
        print("Code recognized: {}".format(code))


