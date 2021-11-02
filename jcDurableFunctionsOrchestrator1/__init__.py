# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.
# Before running this sample, please:
# - create a Durable activity function (default name is "Hello")
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import json
import logging
import os
import pytz
import time
import azure.functions as func
import azure.durable_functions as df
from datetime import datetime, timedelta

# A - jcDurableFunctionsOrchestrator1 : orchestrator_function #

tz_LA = pytz.timezone('America/Los_Angeles') 
datetime_LA = datetime.now(tz_LA)
blob_file_name = os.getenv('blob_file_name') + datetime_LA.strftime("%Y%m%d") + '.png'

def orchestrator_function(context: df.DurableOrchestrationContext):
    #define our orchestration

    json_data_dict: str = context.get_input()
    #dict: type(json_data_dict)

    dataList = json_data_dict['dataImages']

    #return None

    tasks = []
    for oneItem in dataList:
        oneDict = dict(oneItem)
        #logging.info("jcDurableFunctionsOrchestrator1: " + str(oneDict["name"]))
        inputs = []
        inputs.append(blob_file_name)
        inputs.append(oneDict["x1"])
        inputs.append(oneDict["y1"])
        inputs.append(oneDict["x2"])
        inputs.append(oneDict["y2"])
        inputs.append(oneDict["name"])
        inputStr = json.dumps(inputs)
        tasks.append(context.call_activity("jcActivityFunction1", inputStr))

    results = yield context.task_all(tasks)
    return results

#this below line runs on function debugging start
main = df.Orchestrator.create(orchestrator_function)
