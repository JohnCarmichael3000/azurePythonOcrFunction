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
import logging
import os
import time
import azure.functions as func
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from datetime import datetime, timedelta

#
# Azure Function - demonstrate how to use Azure Cognitive Services Computer Vision (OCR) on an image located at a
# specified URL
#

# Main Azure Function
def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('FUNCTION jcPythonOcrFunc HTTP trigger started processing a request.')

    url  = req.params.get('imageUrl')

    if url:
        region = 'westus2'
        cognitive_services_subscription_key = os.getenv('jcVision1Key')

        credentials = CognitiveServicesCredentials(cognitive_services_subscription_key)

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
            time.sleep(1)

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
