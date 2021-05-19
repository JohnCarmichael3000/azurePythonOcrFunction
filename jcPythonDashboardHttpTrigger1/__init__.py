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
import pytz
import requests
import azure.functions as func
from azure.cosmosdb.table.tableservice import TableService
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
from PIL import Image

#
# Azure Function - demonstrate how to use Microsoft Table Storage and Blob Container services to read/save text data and blob data
#
# Documentation References:
#  - Azure Table Service documentation - https://docs.microsoft.com/en-us/azure/storage/tables/
#  - Getting Started with Tables - https://azure.microsoft.com/en-us/documentation/articles/storage-python-how-to-use-table-storage/
#  - Basic Table Samples - https://github.com/Azure-Samples/storage-table-python-getting-started/blob/master/table_basic_samples.py
#  - Advanced Table Samples - https://github.com/Azure-Samples/storage-table-python-getting-started/blob/master/table_advanced_samples.py
#

# Call function running on Azure that identifies text (OCR) in a specified region of an image located at a specified URL location
def ocrFromUrlFunction(urlValue, x1Val, y1Val, x2Val, y2Val):
    ocrFuncUrl = f"{os.getenv('ocrFromImageUrlFncUrl')}&sourceurl={urlValue}&x1={x1Val}&y1={y1Val}&x2={x2Val}&y2={y2Val}"
    logging.info("FUNCTION ocrFuncUrl: " + ocrFuncUrl)

    response = requests.get(ocrFuncUrl, timeout=60)
    ocrFoundValue = response.text
    return ocrFoundValue

def insertDataInTable(tableSvc, tableName, partitionKey, rowKey, itemValue):
    dataPoint = {'PartitionKey': partitionKey, 
            'RowKey': rowKey,
            'Name': itemValue}
    tableSvc.insert_entity(tableName, dataPoint)

# Main Azure Function
def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('FUNCTION jcPythonDashboardHttpTrigger1 HTTP trigger started processing a request.')

    tz_LA = pytz.timezone('America/Los_Angeles') 
    datetime_LA = datetime.now(tz_LA)
    storage_connect_str = os.getenv('psfuncstoraacctAccessKey1')

    #*********************************************************************************************
    #1. call nodeJs jcScreenshot function and save resulting jpg to blob storage, get new blob url
    
    todayFileName = 'dashboard_screenshot_' + datetime_LA.strftime("%Y%m%d") + '.png'

    #sourceurl = os.getenv('dashBoardScreenShotFunctionUrl')
    sourceurl = os.getenv('dashBoardScreenShotTestAsBlob')

    response = requests.get(sourceurl, timeout=120)

    with Image.open(io.BytesIO(response.content)) as im: 

        #im: <class 'PIL.PngImagePlugin.PngImageFile'>
        blob_service_client = BlobServiceClient.from_connection_string(storage_connect_str)
        blob_client = blob_service_client.get_blob_client(container='dashboardblobcontainer', blob=todayFileName)
        
        #need to convert PIL Image to <class 'bytes'> to be able to stream to upload_blob() method 
        imagefile = io.BytesIO()
        im.save(imagefile, format='PNG')
        imagedata = imagefile.getvalue()
        #imagdata: <class 'bytes'>

        #set new blob's content type show it can be downloaded as an image and not just a byte stream
        my_content_settings = ContentSettings(content_type='image/png')

        results = blob_client.upload_blob(imagedata, overwrite=True, content_settings=my_content_settings)
        savedBlobUrl= blob_client.url
        logging.info("FUNCTION blob saved as URL: " + savedBlobUrl)
        blob_client.close()

    table_service = TableService(connection_string=storage_connect_str)
    table_name = 'covidDashboardData'
    rowKeyTime = datetime_LA.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    #*********************************************************************************************
    #2. pass blob url and coorindates to jcPythonOcrFromImgBytesFunc to get OCR values

    totalDoses = ocrFromUrlFunction(savedBlobUrl, 80, 768, 342, 826)
    if (len(totalDoses) > 0):
        insertDataInTable(table_service, table_name, 'totalTests', rowKeyTime, totalDoses)
        logging.info("Found totalDoses value: " + totalDoses + ". Inserting.")
    else:
        logging.info("ERROR with totalDoses, no value was found. Not inserting.")

    totalCases = ocrFromUrlFunction(savedBlobUrl, 76, 91, 342, 159)
    if (len(totalCases) > 0):
        insertDataInTable(table_service, table_name, 'totalTests', rowKeyTime, totalCases)
        logging.info("Found totalCases value: " + totalCases + ". Inserting.")
    else:
        logging.info("ERROR with totalCases, no value was found. Not inserting.")

    return func.HttpResponse("FUNCTION jcPythonDashboardHttpTrigger1 executed successfully by HTTP trigger.", status_code=200)
