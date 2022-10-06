# azurePythonOcrFunction

Various Azure Functions written in Python that use Azure Cognitive Services OCR, Azure Storage, Selenium

1. jcDashboardScreenshotHttpTrigger1
Python - http trigger function. Calls nodeJs Selenium screen shot function and saves image result to blob storage container.

2. jcPythonDashboardHttpTrigger1
Python - http trigger function. Durable Function uses fanout functions pattern to process multiple data regions specified in json stored in Env-var in parallel. Does OCR analysis on each region of image URL (can be any url eg blob storage, internet) and store OCR result text in Azure Table.

  {  "dataImages":
      [
          { "name": "totalCases", "x1": 76, "y1": 91, "x2": 342, "y2": 159, "number": 1 },
          ...
      ]
  }

<img src="https://learn.microsoft.com/en-us/azure/azure-functions/durable/media/durable-functions-concepts/fan-out-fan-in.png" alt="Fan out fan in pattern diagram" style="height: 100px; width:100px;"/>

3. jcPythonOcrFromImgBytesFunc
Python - http trigger function. Demonstrates using Azure Cognitive Services Computer Vision (OCR) on a specified region of an image (x1,y1,x2,y2) stored in a specified URL location. Returning text found in region by OCR.

4. jcPythonOcrFunc
Python - http trigger function. Demonstrates how to use Azure Cognitive Services Computer Vision (OCR) on an image located at input parameter URL location and return text found by OCR

5. jcPythonTimerUrlImageDownload
Python - timer function. Downloads jpg from url in function (env/kv var) and saves to storage account.
