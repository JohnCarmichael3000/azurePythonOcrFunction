#-------------------------------------------------------------------------
# JOHN C - jcPythonDashboardHttpTrigger1
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
import json
import logging
import os
import pytz
import requests
import time
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

counter = 0

# Call function running on Azure that identifies text (OCR) in a specified region of an image located at a specified URL location
def ocrFromUrlFunction(urlValue, x1Val, y1Val, x2Val, y2Val):
    global counter
    ocrFuncUrl = f"{os.getenv('ocrFromImageUrlFncUrl')}&sourceurl={urlValue}&x1={x1Val}&y1={y1Val}&x2={x2Val}&y2={y2Val}"
    counter += 1
    logging.info(f"FUNCTION ocrFuncUrl ({counter}): {ocrFuncUrl}")

    response = requests.get(ocrFuncUrl, timeout=60)
    ocrFoundValue = response.text
    time.sleep(8)
    if (ocrFoundValue.find("404 Not Found") >= 0):
        logging.info("Cognitive service returned 404 not found error")
        return ""
    else:
        return ocrFoundValue

def insertDataInTable(tableSvc, tableName, partitionKey, rowKey, itemValue):
    dataPoint = {'PartitionKey': partitionKey, 
            'RowKey': rowKey,
            'Name': itemValue}
    #tableSvc.insert_entity(tableName, dataPoint)
    tableSvc.insert_or_replace_entity(tableName, dataPoint)

def dataSave(tableSvc, imageUrl, tableName, parKey, rowKeyVal, x1Val, y1Val, x2Val, y2Val):
    global counter
    ocrValue = ocrFromUrlFunction(imageUrl, x1Val, y1Val, x2Val, y2Val)
    if (len(ocrValue) > 0) and (ocrValue.lower().find("error") == -1):
        logging.info(f"FUNCTION for {parKey} ({counter}) found value: {ocrValue}. Inserting. x1Val={x1Val}, y1Val={y1Val}, x2Val={x2Val}, y2Val={y2Val}")
        insertDataInTable(tableSvc, tableName, parKey, rowKeyVal, ocrValue)
    else:
        logging.info(f"FUNCTION ERROR with {parKey} ({counter}), no value was found. Not inserting. x1Val={x1Val}, y1Val={y1Val}, x2Val={x2Val}, y2Val={y2Val}")

# Main Azure Function
def main(req: func.HttpRequest) -> func.HttpResponse:
    
    logging.info('FUNCTION jcPythonDashboardHttpTrigger1 HTTP trigger started processing a request.')

    storage_connect_str = os.getenv('psfuncstoraacctAccessKey1')
    tz_LA = pytz.timezone('America/Los_Angeles') 
    datetime_LA = datetime.now(tz_LA)
    isOnAzure = os.getenv('WEBSITE_INSTANCE_ID')

    logging.info("******************************************************************************************************")
    logging.info("FUNCTION 1. call nodeJs jcScreenshot function and save resulting jpg to blob storage, get new blob url")
    
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
        time.sleep(3)

    logging.info("******************************************************************************************************")
    logging.info("2. pass blob url and coorindates to jcPythonOcrFromImgBytesFunc to get OCR values")

    table_service = TableService(connection_string=storage_connect_str)
    table_name = os.getenv('dashboardFunctionTableName')
    rowKeyTime = datetime_LA.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    json_data = "dataString"
    if len(isOnAzure) > 0:
        json_data = json.loads(os.getenv('dashboardDataNames'))
    else:
        with open('C:\json_data.txt','r') as file:
            jsonDataFromFile = file.read()
            json_data = json.loads(jsonDataFromFile)

    #JSON data format:
    """
    {  "dataImages":
        [
            { "name": "sample1", "x1": 76, "y1": 91, "x2": 342, "y2": 159, "number": 1},
            ...
        ]
    }
    """

    dataList = json_data["dataImages"] 
    for oneItem in dataList:
        oneDict = dict(oneItem)
        #logging.info(str(oneDict["name"]))
        dataSave(table_service, savedBlobUrl, table_name, oneDict["name"], rowKeyTime, oneDict["x1"], oneDict["y1"], oneDict["x2"], oneDict["y2"])
        logging.info(" ")

    returnMsg = "FUNCTION jcPythonDashboardHttpTrigger1 executed successfully by HTTP trigger."
    logging.info(returnMsg)
    return func.HttpResponse(returnMsg, status_code=200)
