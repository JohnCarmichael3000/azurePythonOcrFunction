import logging
import azure.functions as func
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from datetime import datetime, timedelta
import time
import os

def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    url  = req.params.get('imageUrl')

    if url:
        region = 'westus2'
        key = os.getenv('jcVision1Key')

        logging.info('before credentials')
        credentials = CognitiveServicesCredentials(key)

        #create client
        client = ComputerVisionClient(
            endpoint="https://" + region + ".api.cognitive.microsoft.com/",
            credentials=credentials
        )
        raw = True
        numberOfCharsInOperationId = 36

        logging.info('before client.read')
        rawHttpResponse = client.read(url, language="en", raw=True)

        # Get ID from returned headers
        operationLocation = rawHttpResponse.headers["Operation-Location"]
        idLocation = len(operationLocation) - numberOfCharsInOperationId
        operationId = operationLocation[idLocation:]

        # SDK call
        while True:
            result = client.get_read_result(operationId)
            if result.status.lower () not in ['notstarted', 'running']:
                break
            logging.info('Waiting for result...')
            time.sleep(5)

        # Get data
        if result.status == OperationStatusCodes.succeeded:
            logging.info('result.status = OperationStatusCodes.succeeded')
            for line in result.analyze_result.read_results[0].lines:
                logging.info('OCR image analysis found text:')
                logging.info(line.text)
                return func.HttpResponse(line.text)
        else:
            logging.info('result.status != OperationStatusCodes.succeeded. result.status is:')
            logging.info(result.status)
            return func.HttpResponse(f"Error result.status was: " + result.status + '\n' + str(datetime.now() + timedelta(hours=-12)))

    else:
        msg = 'This HTTP triggered function executed successfully. Pass a imageUrl parameter for OCR analysis.'
        logging.info(msg)
        return func.HttpResponse(
             msg,
             status_code=200
        )
