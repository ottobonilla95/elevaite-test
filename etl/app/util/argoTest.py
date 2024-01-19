from pprint import pprint

import argo_workflows
from argo_workflows.api import workflow_service_api
from argo_workflows.model.container import Container
from argo_workflows.model.io_argoproj_workflow_v1alpha1_template import IoArgoprojWorkflowV1alpha1Template
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow import IoArgoprojWorkflowV1alpha1Workflow
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_create_request import (
    IoArgoprojWorkflowV1alpha1WorkflowCreateRequest,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_spec import (
    IoArgoprojWorkflowV1alpha1WorkflowSpec,
)
from argo_workflows.model.object_meta import ObjectMeta

token_value = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImJWSmRiTktpcnRYTkFfcGpBdlBmWU43NTdsWlhTYjlZWmpRMGN2UHRhREkifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImV0bC5zZXJ2aWNlLWFjY291bnQtdG9rZW4iLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZXRsIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiZWE1OThiZjUtYTFhNy00MDg1LWIxYTYtOGI1YWZlMTA3ZTQzIiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmRlZmF1bHQ6ZXRsIn0.oHrZNvwqXm5qjN_Oe_2BoI9PDwBCh5GekOWWz-DgDJQiUSDbBcqrZQZ_WyaI50dH6fzzmeUI4-F7AdXfXpc075c-5UPDQbAw4KDBVZ3h9fVHoC99mQcS7q5augfwYe8dujFXbvtUtRgiprNfE9fx31eeygqJY5HChVnoGLQsONaycWVFUpiReaVSSLDMiHqW28yQhx7r7IofwWv4EG5nTK5575a2hl84iVKYmXhXaoepGgy-9CFZdx0kAkaHdoo7UVnmRZUz4Vh_xKxAwvhX4tez7BsE6g6-frvQ3GkuGI28h4qgOqT2TmazKVwr-OjHh4Ro4oitt0uRvm1iQL_19g"
access_token = f"Bearer {token_value}"

configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746")
configuration.verify_ssl = False

manifest = IoArgoprojWorkflowV1alpha1Workflow(
    metadata=ObjectMeta(generate_name='hello-world-'),
    spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
        entrypoint='whalesay',
        templates=[
            IoArgoprojWorkflowV1alpha1Template(
                name='whalesay',
                container=Container(
                    image='docker/whalesay:latest', command=['cowsay'], args=['hello world']))]))

api_client = argo_workflows.ApiClient(configuration)
api_client.set_default_header("Authorization", access_token)
api_instance = workflow_service_api.WorkflowServiceApi(api_client)

# if __name__ == '__main__':
#     api_response = api_instance.create_workflow(
#         namespace='argo',
#         body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
#         _check_return_type=False)
#     pprint(api_response)


def create_test_workflow():
    api_response = api_instance.create_workflow(
        namespace='argo',
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False)
    pprint(api_response)
    return str(api_response)
