import io
import logging
import requests
import os
import pytz
import time
import azure.functions as func
from azure.cosmosdb.table.tableservice import TableService
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
from PIL import Image

def main(req: func.HttpRequest) -> func.HttpResponse:

    #jcDashboardScreenshotHttpTrigger1
    logging.info('Python HTTP trigger function processed a request.')

    tz_LA = pytz.timezone('America/Los_Angeles') 
    datetime_LA = datetime.now(tz_LA)

    storage_connect_str = os.getenv('psfuncstoraacctAccessKey1')

    logging.info("******************************************************************************************************")
    logging.info("FUNCTION 1. call nodeJs jcScreenshot function and save resulting jpg to blob storage, get new blob url")
    
    todayFileName = 'dashboard_screenshot_' + datetime_LA.strftime("%Y%m%d") + '.png'

    #from screen shot stored as blob - for testing
    #sourceurl = os.getenv('dashBoardScreenShotTestAsBlob')

    #take current screen shot using screen shot function
    sourceurl = os.getenv('dashBoardScreenShotFunctionUrl')
    
    logging.info("FUNCTION getting screen shot via screen shot function url:")
    logging.info(sourceurl)

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

    return func.HttpResponse("This HTTP triggered function executed successfully.", status_code=200)
