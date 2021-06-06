#-------------------------------------------------------------------------
# jcPythonTimerUrlImageDownload
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
import requests
import os
import pytz
import time
import azure.functions as func
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
from PIL import Image

#
# Azure Function - demonstrate using Azure Storage Blobs saving an image at a specified URL to a blob container
# Using all-memory operations as this is running in a serverless function where disk operations would not be
# preferable and/or not permitted.
#
# Documentation References:
#  - Azure Storage Blobs client library for Python:
#    https://docs.microsoft.com/en-us/python/api/overview/azure/storage-blob-readme?view=azure-python
#  - Quickstart: Manage blobs with Python v12 SDK
#    https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python
#

def main(mytimer: func.TimerRequest) -> None:

    tz_LA = pytz.timezone('America/Los_Angeles') 
    datetime_LA = datetime.now(tz_LA)

    todayFileName = 'image_' + datetime_LA.strftime("%Y%m%d") + '.jpg'

    containerName = os.getenv('image_to_dl_container_name')
    sourceurl = os.getenv('image_to_dl_url')
    response = requests.get(sourceurl, timeout=120)
    storage_connect_str = os.getenv('psfuncstoraacctAccessKey1')

    with Image.open(io.BytesIO(response.content)) as im: 

        blob_service_client = BlobServiceClient.from_connection_string(storage_connect_str)
        blob_client = blob_service_client.get_blob_client(container=containerName, blob=todayFileName)
        
        #need to convert PIL Image to <class 'bytes'> to be able to stream to upload_blob() method 
        imagefile = io.BytesIO()
        im.save(imagefile, format='jpeg')
        imagedata = imagefile.getvalue()
        #imagdata: <class 'bytes'>

        #set new blob's content type show it can be downloaded as an image and not just a byte stream
        my_content_settings = ContentSettings(content_type='image/jpg')

        results = blob_client.upload_blob(imagedata, overwrite=True, content_settings=my_content_settings)
        savedBlobUrl= blob_client.url
        logging.info("FUNCTION blob saved as URL: " + savedBlobUrl)
        blob_client.close()
