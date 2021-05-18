
import azure.functions as func
from PIL import Image
import logging
import os
import requests
import io
import time


def main(req: func.HttpRequest) -> func.HttpResponse:

    #https://stackoverflow.com/questions/65326103/pil-image-as-bytes-with-bytesio-to-prevent-hard-disk-saving
    #https://github.com/Azure/azure-sdk-for-python/blob/f40a0ffe9bfa6843370ce3c1979021cc7b0bfb99/sdk/cognitiveservices/azure-cognitiveservices-vision-computervision/azure/cognitiveservices/vision/computervision/operations/_computer_vision_client_operations.py#L1505

    logging.info('Python jcPythonOcrFromImgBytesFunc HTTP trigger function processed a request.')
    
    sourceurl = os.getenv('sourceurl')

    region = 'westus2'
    endpoint="https://" + region + ".api.cognitive.microsoft.com"
    subscription_key = os.getenv('jcVision1Key')

    url = endpoint+"/vision/v3.1/read/analyze"
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'application/octet-stream'
    }
    
    response = requests.get(sourceurl)

    with Image.open(io.BytesIO(response.content)) as im:  #im: <class 'PIL.PngImagePlugin.PngImageFile'>

        box = (80,768,342,826)
        region = im.crop(box) # region: <class 'PIL.Image.Image'>

        with io.BytesIO() as buf:

            region.save(buf, 'jpeg')
            response = requests.request("POST", url, headers=headers, data=buf.getvalue())
            
            # get result
            while True:

                res = requests.request("GET", response.headers['Operation-Location'], headers=headers)
                status = res.json()['status']

                if status == 'succeeded':
                    #print(res.json()['analyzeResult'])
                    resultJson = res.json()
                    foundText = resultJson.get("analyzeResult").get("readResults")[0].get("lines")[0].get("text")
                    logging.info("FOUND TEXT:")
                    logging.info(foundText)
                    break
                time.sleep(1)

        return foundText
