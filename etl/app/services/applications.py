from datetime import datetime
from pprint import pprint
import uuid

from ..util.models import (
    ApplicationFormDTO,
    ApplicationInstanceDTO,
    ApplicationPipelineDTO,
    CreateApplicationInstanceDTO,
    IngestApplicationDTO,
    InstanceStatus,
)
from ..util.mockData import applications_list


def getApplicationList() -> list[IngestApplicationDTO]:
    return map(lambda x: x.toDto(), applications_list)


def getApplicationById(application_id: str) -> IngestApplicationDTO:
    return list(filter(lambda x: x.id == application_id, applications_list))[0].toDto()


def getApplicationForm(application_id: str) -> ApplicationFormDTO:
    return list(filter(lambda x: x.id == application_id, applications_list))[0].form


def getApplicationInstances(application_id: str) -> list[ApplicationInstanceDTO]:
    return list(filter(lambda x: x.id == application_id, applications_list))[
        0
    ].instances


def getApplicationPipelines(application_id: str) -> list[ApplicationPipelineDTO]:
    return list(filter(lambda x: x.id == application_id, applications_list))[
        0
    ].pipelines


def getApplicationInstanceById(
    application_id: str, instance_id: str
) -> ApplicationInstanceDTO:
    application_instances = list(
        filter(lambda x: x.id == application_id, applications_list)
    )[0].instances
    return list(filter(lambda x: x.id == instance_id, application_instances))[0]


def createApplicationInstance(
    application_id: str, createApplicationInstanceDto: CreateApplicationInstanceDTO
) -> ApplicationInstanceDTO:
    instance = ApplicationInstanceDTO(
        creator=createApplicationInstanceDto.creator,
        startTime=datetime.utcnow().isoformat(),
        endTime=None,
        id=uuid.uuid4().urn[9:],
        status=InstanceStatus.STARTING,
    )
    application = list(filter(lambda x: x.id == application_id, applications_list))[0]
    application_index = applications_list.index(application)
    application.instances.append(instance)
    applications_list[application_index] = application

    return instance
