import os
import time

from dbos import DBOS, DBOSConfig, SetWorkflowID
import dotenv
from starlette.responses import JSONResponse
from query_classification import QueryClassifier
from data_classes import QueryClassificationResult, QueryClassificationRequest
import uuid
from database_connection import DatabaseConnection

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    dotenv.load_dotenv(".env.local")

# Welcome to DBOS!
# This is a template application built with DBOS and FastAPI.
# It shows you how to use DBOS to build durable workflows that are resilient to any failure.

config: DBOSConfig = {
    "name": "dbos-app-query-classification",
    "system_database_url": os.environ.get("DBOS_SYSTEM_DATABASE_URL"),
}
DBOS(config=config)
DBOS.launch()



steps_event = "steps_event"

def launch_durable_workflow(request: QueryClassificationRequest):
    task_id = str(request.qid)
    print("Task ID: ", task_id)
    with SetWorkflowID(str(task_id)):
        DBOS.start_workflow(workflow, task_id)
    return JSONResponse(
        status_code=202,
        content={"status": "started", "task_id": task_id, "status_url": f"/last_step/{task_id}"},
    )


# Here is the code for a durable workflow with three steps.
# DBOS workflows are resilient to any failure--if your program is crashed,
# interrupted, or restarted while running this workflow, the workflow
# automatically resumes from the last completed step.

# One interesting implementation detail: we use set_event to publish the workflow's
# status to the frontend after each step completes, so you can observe what your workflow
# is doing in real time.


@DBOS.step(retries_allowed=True, max_attempts=3)
async def step_one(qid: str):
    print("Query ID: ", qid)
    # Get original request from database
    db_connection = DatabaseConnection()
    original_request = None
    try:
        original_request = await db_connection.get_query_request(qid)
    except Exception as e:
        print(f"Error fetching query request: {e}")
        return
    time.sleep(1)
    if not original_request:
        print("Original request not found.")
        return
    print("Original Request: ", original_request)
    print("Original Request Text: ", getattr(original_request, "original_request", None))
    print("Reformulated Request: ", getattr(original_request, "request", None))

    await db_connection.close_db()
    return getattr(original_request, "request", None)



@DBOS.step(retries_allowed=True, max_attempts=3, interval_seconds=5)
async def step_two(qid: str, query_text: str):
    classifier = QueryClassifier()
    result = classifier.classify_query(query_text)
    print("Classification Result: ", result)
    res = QueryClassificationResult(
                                    query_id=qid,
                                    query_type=result["query_type"],
                                    machine_type=result["machine_type"],
                                    machine_model=result["machine_model"],
                                    machine_name=result["machine_name"],
                                    customer_name=result["customer_name"],

                                    )
    print("Query Classification Result: ", res)
    db_connection = DatabaseConnection()
    await db_connection.save_query_classification(uuid.UUID(qid), res)
    print("Query Classification Result Saved")
    await db_connection.close_db()



@DBOS.workflow()
async def workflow(qid: str):
    original_query_text = await step_one(qid)
    DBOS.set_event(steps_event, 1)
    print("Original Query Text: ", original_query_text)
    if original_query_text:
        await step_two(qid, original_query_text)
        DBOS.set_event(steps_event, 2)
    else:
        # Workflow failed
        print("Original query text not found. Workflow failed.")
        DBOS.set_event(steps_event, 3)




# This endpoint retrieves the status of a specific durable workflow.


def get_last_completed_step(task_id: str):
    try:
        step = DBOS.get_event(task_id, steps_event, timeout_seconds=0)
    except KeyError:  # If the task hasn't started yet
        return 0
    return step if step is not None else 0


# This endpoint crashes the application. For demonstration purposes only :)


def crash_application():
    os._exit(1)

