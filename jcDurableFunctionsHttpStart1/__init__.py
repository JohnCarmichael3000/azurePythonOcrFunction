# This function an HTTP starter function for Durable Functions.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable activity function (default name is "Hello")
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt
 
import logging
import json
import azure.functions as func
import azure.durable_functions as df

# B? jcDurableFunctionsHttpStart1 - Client function (HTTP starter) #

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:

    #this is the first line run after http request is made
    client = df.DurableOrchestrationClient(starter)
    payload: str = json.loads(req.get_body().decode()) # Load JSON post request data
    instance_id = await client.start_new(req.route_params["functionName"], client_input=payload)

    logging.info(f"Started orchestration with ID = '{instance_id}'.")

    #this causes A:jcDurableFunctionsOrchestrator1 - orchestrator_function to run
    return client.create_check_status_response(req, instance_id)
