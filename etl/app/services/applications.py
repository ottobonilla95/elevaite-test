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
    ApplicationInstancePipelineStepStatus,
    ApplicationPipelineDTO,
    ApplicationType,
    IngestApplication,
    IngestApplicationChartDataDTO,
    IngestApplicationDTO,
    InstanceStatus,
    PipelineStepStatus,
    PreProcessFormDTO,
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
    createApplicationInstanceDto: S3IngestFormDataDTO | PreProcessFormDTO,
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
        datasetId=instanceID,
        name=createApplicationInstanceDto.name,
        pipelineStepStatuses=[],
        comment=None,
    )
    res = elasticClient.getById("application", application_id)
    application = IngestApplication(**res["_source"])
    pprint(application.instances)

    if (
        application.applicationType == ApplicationType.PREPROCESS
        and createApplicationInstanceDto.selectedPipeline
    ):
        if len(application.pipelines) > 0:
            _pipeline = None
            for p in application.pipelines:
                if p.id == createApplicationInstanceDto.selectedPipeline:
                    _pipeline = p

            if _pipeline == None:
                instance.comment = "Pipeline was not found."
                instance.status = InstanceStatus.FAILED
            else:
                instance.selectedPipeline = (
                    createApplicationInstanceDto.selectedPipeline
                )
                for pl in _pipeline.steps:
                    _status = PipelineStepStatus.IDLE
                    if pl.id == _pipeline.entry:
                        _status = PipelineStepStatus.RUNNING
                    instance.pipelineStepStatuses.append(
                        ApplicationInstancePipelineStepStatus(
                            status=_status, step=pl.id
                        )
                    )

    application.instances.append(instance)
    instances = application.instances
    # instances.append(instance.dict())
    pprint(application.instances)

    elasticClient.client.update(
        index="application",
        id=application_id,
        body=json.dumps({"doc": {"instances": instances}}, default=vars),
    )

    if instance.status == InstanceStatus.FAILED:
        raise Exception("Instance creation failed. See comment for reason")

    _data = {
        "id": instanceID,
        "dto": createApplicationInstanceDto,
        "application_id": application_id,
    }

    def get_routing_key(application_id) -> str:
        match application_id:
            case "1":
                return "s3_ingest"
            case "2":
                return "preprocess"
            case _:
                return "default"

    # rmq = RabbitMQSingleton()
    rmq.channel().basic_publish(
        exchange="",
        body=json.dumps(_data, default=vars),
        routing_key=get_routing_key(application_id=application_id),
    )

    return instance


def approveApplicationInstance(
    application_id: str, instance_id: str
) -> ApplicationInstanceDTO:
    elasticClient = ElasticSingleton()
    res = elasticClient.getById("application", application_id)
    app = IngestApplication(**res["_source"])
    _instance = None

    # TODO: Think about adding an exit pointer to the pipeline. It will probably make things much much simpler
    for instance in app.instances:
        if instance.id == instance_id:
            pipeline = list(
                filter(lambda x: x.id == instance.selectedPipeline, app.pipelines)
            )[0]
            dependedOn = []
            for ps in pipeline.steps:
                dependedOn.extend(ps.dependsOn)

            for pss in instance.pipelineStepStatuses:
                if pss.step not in dependedOn:
                    pss.endTime = datetime.utcnow().isoformat()
            _instance = instance
            break

    elasticClient.client.update(
        index="application",
        id=application_id,
        body=json.dumps({"doc": {"instances": app.instances}}, default=vars),
    )
    return _instance


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
            ingestedChunks=res["ingested_chunks"],
        )
