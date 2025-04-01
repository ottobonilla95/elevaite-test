from .s3_initialization import S3Initialization
from .s3_worker import S3WorkerStep
from .service_now_worker import ServiceNowWorker
from .servicenow_initialization import ServiceNowInitialization
from .base_step import register_step


register_step(step_id="9966b76c-5a5a-4eeb-924f-bd5983b4610a", cls=S3Initialization)
register_step(step_id="9fb4ebe8-a679-40a7-90a7-e14f26e6f397", cls=S3WorkerStep)
register_step(
    step_id="e97d9ddc-707e-47a4-8a15-00ca8c00f5fb", cls=ServiceNowInitialization
)
register_step(step_id="0daffa6c-653c-46c5-b511-eac4f6d91333", cls=ServiceNowWorker)
