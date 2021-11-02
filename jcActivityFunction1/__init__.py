# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import io
import json
import logging
import os
import pathlib
import requests
import time
from PIL import Image

# C - ACTIVITY FUNCTION #

def main(souceValues: str) -> str:

    sourceValuesList = souceValues.split(', ')
    sourceurl = sourceValuesList[0][2:-1]
    x1 = int(sourceValuesList[1])
    y1 = int(sourceValuesList[2])
    x2 = int(sourceValuesList[3])
    y2 = int(sourceValuesList[4])
    dataName = sourceValuesList[5][1:-2]

    #the activity. 
    minDimensionSize = 50 #Az OCR needs minimum size image
    if (x2 - x1) < minDimensionSize:
        print('Minimum region size problem for ' + dataName + ' x value width of ' + str(x2 - x1) + ' less than min of ' + str(minDimensionSize) \
            + ' setting to ' + str(x1) + ', ' + str(x1 + minDimensionSize))
        x2 = (x1 + minDimensionSize)

    if (y2 - y1) < minDimensionSize:
        print('Minimum region size problem for ' + dataName + ' y value width of ' + str(y2 - y1) + ' less than min of ' + str(minDimensionSize) \
            + ' setting to ' + str(y1) + ', ' + str(y1 + minDimensionSize))
        y2 = (y1 + minDimensionSize)

    logging.info("JC Activity Function: " + dataName + " " + str(x1) + ", " + str(y1) + ", " + str(x2) + ", " + str(y2) + ", " "url: " + sourceurl)

    region = 'westus2'
    endpoint="https://" + region + ".api.cognitive.microsoft.com"
    cognitive_services_subscription_key = os.getenv('jcVision1Key')

    url = endpoint+"/vision/v3.1/read/analyze"
    headersToUse = {
        'Ocp-Apim-Subscription-Key': cognitive_services_subscription_key,
        'Content-Type': 'application/octet-stream'
    }

    #Supported file formats: JPEG, PNG, BMP, PDF, and TIFF. This function uses image manipulation so only image formats are accepted, not PDF.
    #Reference: https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/overview-ocr#input-requirements
    file_ext = pathlib.Path(sourceurl).suffix.lower()
    accepted_ext = [".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif"]
    if (file_ext not in accepted_ext):
        errMsg = "Only " + str(accepted_ext) + " file types are accepted."
        raise logging.exception(errMsg)

    #logging.info("FUNCTION request.get sourceurl...")
    response = requests.get(sourceurl, timeout=120)

    with Image.open(io.BytesIO(response.content)) as im:

        #im: <class 'PIL.PngImagePlugin.PngImageFile'>
        box = (x1,y1,x2,y2)

        #region: <class 'PIL.Image.Image'>
        region = im.crop(box) 

        with io.BytesIO() as buf:

            #buf: <class '_io.BytesIO'>
            region.save(buf, file_ext.replace('.', ''))

            dataToUse = buf.getvalue()
            #dataToUse:  <class 'bytes'>

            #logging.info("Input Data length in Bytes: " + str(len(dataToUse)))

            #post request to endpoint with 
            response = requests.request("POST", url, headers=headersToUse, data=dataToUse)
            #logging.info("FUNCTION response.status_code: " + str(response.status_code))
            if (response.status_code != 202):
                logging.info("FUNCTION ERROR - response.content:\n" + str(response.content))
                logging.info("FUNCTION ERROR - response.content:\n" + str(response.headers))
                return "ERROR: " + str(response.status_code)
            
            # get OCR result from endpoint, check for completion one per second 
            while True:
                res = requests.request("GET", response.headers['Operation-Location'], headers=headersToUse)

                resTest = res.status_code
                if resTest == 429:
                    #429 
                    #b'{"error":{"code":"429","message": "Requests to the Get Read Result Operation under Computer Vision API (v3.1) have exceeded 
                    #rate limit of your current ComputerVision S1 pricing tier. Please retry after 1 second. Please contact Azure support service if 
                    #you would like to further increase the default rate limit."}}'
                    time.sleep(5)
                    res = requests.request("GET", response.headers['Operation-Location'], headers=headersToUse)

                status = res.json()['status']

                if status == 'succeeded':
                    resultJson = res.json()
                    foundText = resultJson.get("analyzeResult").get("readResults")[0].get("lines")[0].get("text")
                    #logging.info("FUNCTION found text: " + foundText)
                    break
                elif status == 'failed':
                    errMsg = f"FUNCTION received failed error from endpoint '{url}'"
                    raise logging.exception(errMsg)

                time.sleep(2)

    output = []
    output.append(dataName)
    output.append(foundText)
    return json.dumps(output)


