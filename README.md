# azurePythonOcrFunction

Azure Functions written in Python that use Azure Cognitive Services OCR:

1. jcDashboardScreenshotHttpTrigger1
  Python - http trigger function. Calls nodeJs screen shot function and saves image result to blob storage container.

2. jcPythonDashboardHttpTrigger1
  Python - http trigger function. Loops through data regions specified in json stored in Env-var to do OCR analysis on each region of image URL (can be any url eg blob storage, internet) and store 
  OCR result text in Azure Table.

  {  "dataImages":
      [
          { "name": "totalCases", "x1": 76, "y1": 91, "x2": 342, "y2": 159, "number": 1 },
          ...
      ]
  }

3. jcPythonOcrFromImgBytesFunc
  Python - http trigger function. Demonstrates using Azure Cognitive Services Computer Vision (OCR) on a specified region of an image (x1,y1,x2,y2) stored in a specified URL location.
  Returning text found in region by OCR.

4. jcPythonOcrFunc
  Python - http trigger function. Demonstrates how to use Azure Cognitive Services Computer Vision (OCR) on an image located at input parameter URL location and return text found by OCR

5. jcPythonTimerUrlImageDownload
  Python - timer function. Downloads jpg from url in function (env/kv var) and saves to storage account.
