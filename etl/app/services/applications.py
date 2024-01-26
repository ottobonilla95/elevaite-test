from datetime import datetime
import json
from pprint import pprint
import uuid

from ..util.RedisSingleton import RedisSingleton

from ..util.RabbitMQSingleton import RabbitMQSingleton

from ..util.models import (
    ApplicationFormDTO,
    ApplicationInstanceDTO,
    ApplicationPipelineDTO,
    IngestApplicationChartDataDTO,
    IngestApplicationDTO,
    InstanceStatus,
    S3IngestFormDataDTO,
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
    application_id: str, createApplicationInstanceDto: S3IngestFormDataDTO
) -> ApplicationInstanceDTO:
    instanceID = uuid.uuid4().urn[33:]
    instance = ApplicationInstanceDTO(
        creator=createApplicationInstanceDto.creator,
        startTime=datetime.utcnow().isoformat(),
        endTime=None,
        id=instanceID,
        status=InstanceStatus.STARTING,
        initialChartData=IngestApplicationChartDataDTO(),
    )
    application = list(filter(lambda x: x.id == application_id, applications_list))[0]
    application_index = applications_list.index(application)
    application.instances.append(instance)
    applications_list[application_index] = application

    _data = {"id": instanceID, "dto": createApplicationInstanceDto}

    rmq = RabbitMQSingleton()
    rmq.channel.basic_publish(
        exchange="",
        body=json.dumps(_data, default=vars),
        routing_key="s3_ingest",
    )

    return instance


def getApplicationInstanceChart(
    application_id: str, instance_id: str
) -> IngestApplicationChartDataDTO:
    r = RedisSingleton().connection

    if r.ping():
        res = r.json().get(instance_id)

        pprint(res)
        return IngestApplicationChartDataDTO(
            avgSize=res["avg_size"],
            ingestedItems=res["ingested_items"],
            totalItems=res["total_items"],
            totalSize=res["total_size"],
            ingestedSize=res["ingested_size"],
        )
