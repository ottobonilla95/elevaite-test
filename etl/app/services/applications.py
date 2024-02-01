from datetime import datetime
import json
from pprint import pprint
import uuid

import pika
from ..util.ElasticSingleton import ElasticSingleton
from ..util.RedisSingleton import RedisSingleton
from ..util.RabbitMQSingleton import RabbitMQSingleton
from ..util.models import (
    ApplicationFormDTO,
    ApplicationInstanceDTO,
    ApplicationPipelineDTO,
    IngestApplication,
    IngestApplicationChartDataDTO,
    IngestApplicationDTO,
    InstanceStatus,
    S3IngestFormDataDTO,
)
from ..util.mockData import applications_list


def getApplicationList() -> list[IngestApplicationDTO]:
    elasticClient = ElasticSingleton()
    res: list[IngestApplicationDTO] = []
    for entry in elasticClient.getAllInIndex("application"):
        print(IngestApplicationDTO(**entry))
        res.append(IngestApplicationDTO(**entry))
    # return map(lambda x: x.toDto(), applications_list)
    return res


def getApplicationById(application_id: str) -> IngestApplicationDTO:
    elasticClient = ElasticSingleton()
    res = elasticClient.getById("application", application_id)
    return IngestApplicationDTO(**res["_source"])


def getApplicationForm(application_id: str) -> ApplicationFormDTO:
    elasticClient = ElasticSingleton()
    res = elasticClient.getById("application", application_id)
    app = IngestApplication(**res["_source"])
    return app.form


def getApplicationInstances(application_id: str) -> list[ApplicationInstanceDTO]:
    elasticClient = ElasticSingleton()
    res = elasticClient.getById("application", application_id)
    app = IngestApplication(**res["_source"])
    return app.instances


def getApplicationPipelines(application_id: str) -> list[ApplicationPipelineDTO]:
    elasticClient = ElasticSingleton()
    res = elasticClient.getById("application", application_id)
    app = IngestApplication(**res["_source"])
    return app.pipelines


def getApplicationInstanceById(
    application_id: str, instance_id: str
) -> ApplicationInstanceDTO:
    elasticClient = ElasticSingleton()
    res = elasticClient.getById("application", application_id)
    application_instances = IngestApplication(**res["_source"]).instances
    print(application_instances)
    return list(filter(lambda x: x.id == instance_id, application_instances))[0]


def createApplicationInstance(
    application_id: str,
    createApplicationInstanceDto: S3IngestFormDataDTO,
    rmq: pika.BlockingConnection,
) -> ApplicationInstanceDTO:
    elasticClient = ElasticSingleton()
    instanceID = uuid.uuid4().urn[33:]
    instance = ApplicationInstanceDTO(
        creator=createApplicationInstanceDto.creator,
        startTime=datetime.utcnow().isoformat(),
        endTime=None,
        id=instanceID,
        status=InstanceStatus.STARTING,
        chartData=IngestApplicationChartDataDTO(),
    )
    res = elasticClient.getById("application", application_id)
    application = IngestApplication(**res["_source"])
    pprint(application.instances)
    application.instances.append(instance)
    instances = application.instances
    # instances.append(instance.dict())
    pprint(application.instances)

    elasticClient.client.update(
        index="application",
        id=application_id,
        body=json.dumps({"doc": {"instances": instances}}, default=vars),
    )

    pprint(elasticClient.getById("application", application_id)["_source"])

    _data = {
        "id": instanceID,
        "dto": createApplicationInstanceDto,
        "application_id": application_id,
    }

    # rmq = RabbitMQSingleton()
    rmq.channel().basic_publish(
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
