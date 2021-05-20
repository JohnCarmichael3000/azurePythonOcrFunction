#-------------------------------------------------------------------------
# JOHN C
#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, 
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES 
# OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
#----------------------------------------------------------------------------------
# The example companies, organizations, products, domain names,
# e-mail addresses, logos, people, places, and events depicted
# herein are fictitious. No association with any real company,
# organization, product, domain name, email address, logo, person,
# places, or events is intended or should be inferred.
#--------------------------------------------------------------------------
import io
import logging
import os
import pathlib
import requests
import time
import azure.functions as func
from PIL import Image

#
# Azure Function - demonstrate using Azure Cognitive Services Computer Vision (OCR) on a specified region of an image stored
# in a specified URL location. Using all-memory operations as this is running in a serverless function where disk operations would not be
# preferable and/or not permitted.
#
# Documentation References:
#  - PIL Image to bytes question: https://stackoverflow.com/questions/65326103/pil-image-as-bytes-with-bytesio-to-prevent-hard-disk-saving
#  - Azure SKD for Python _computer_vision_client_operations.py:
#    https://github.com/Azure/azure-sdk-for-python/blob/f40a0ffe9bfa6843370ce3c1979021cc7b0bfb99/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision/azure/cognitiveservices/vision/computervision/operations/_computer_vision_client_operations.py#L1505
#

# Main Azure Function
def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('FUNCTION jcPythonOcrFromImgBytesFunc HTTP trigger started processing a request.')
    
    sourceurl = req.params.get('sourceurl')

    x1 = int(req.params.get('x1'))
    y1 = int(req.params.get('y1'))
    x2 = int(req.params.get('x2'))
    y2 = int(req.params.get('y2'))

    minDimensionSize = 50
    if (x2 - x1) < minDimensionSize:
        print('FUNCTION X-Dimenion Minimum size problem')
        x2 = (x1 + minDimensionSize)

    if (y2 - y1) < minDimensionSize:
        print('FUNCTION Y-Dimenion Minimum size problem')
        y2 = (y1 + minDimensionSize)

    logging.info("FUNCTION sourceurl: " + sourceurl)
    logging.info(f"x1={x1} y1={y1} x2={x2} y2={y2}")

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

    logging.info("FUNCTION request.get sourceurl...")
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

            logging.info("dataToUse length: " + str(len(dataToUse)))

            #post request to endpoint with 
            response = requests.request("POST", url, headers=headersToUse, data=dataToUse)
            logging.info("FUNCTION response.status_code: " + str(response.status_code))
            if (response.status_code != 202):
                logging.info("FUNCTION ERROR - response.content:\n" + str(response.content))
                logging.info("FUNCTION ERROR - response.content:\n" + str(response.headers))
                return func.HttpResponse("FUNCTION ERROR", status_code=response.status_code) 
            
            # get OCR result from endpoint, check for completion one per second 
            while True:
                res = requests.request("GET", response.headers['Operation-Location'], headers=headersToUse)
                status = res.json()['status']

                if status == 'succeeded':
                    resultJson = res.json()
                    foundText = resultJson.get("analyzeResult").get("readResults")[0].get("lines")[0].get("text")
                    logging.info("FUNCTION found text: " + foundText)
                    break
                elif status == 'failed':
                    errMsg = f"FUNCTION received failed error from endpoint '{url}'"
                    raise logging.exception(errMsg)

                time.sleep(1)

        return func.HttpResponse(foundText, status_code=200)
