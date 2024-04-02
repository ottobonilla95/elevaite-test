class S3IngestData:
    creator: str
    name: str
    projectId: str
    version: str | None
    parent: str | None
    outputURI: str | None
    datasetId: str
    selectedPipelineId: str
    configurationName: str
    isTemplate: bool
    description: str | None
    url: str
    useEC2: bool
    roleARN: str
    applicationId: str
    instanceId: str

    def __init__(
        self,
        creator: str,
        name: str,
        projectId: str,
        version: str | None,
        parent: str | None,
        outputURI: str | None,
        datasetId: str,
        selectedPipelineId: str,
        configurationName: str,
        isTemplate: bool,
        type: str,
        description: str | None,
        url: str,
        useEC2: bool,
        roleARN: str,
        applicationId: str,
        instanceId: str,
    ) -> None:
        self.creator = creator
        self.name = name
        self.projectId = projectId
        self.version = version
        self.parent = parent
        self.outputURI = outputURI
        self.datasetId = datasetId
        self.selectedPipelineId = selectedPipelineId
        self.configurationName = configurationName
        self.isTemplate = isTemplate
        self.description = description
        self.url = url
        self.useEC2 = useEC2
        self.roleARN = roleARN
        self.applicationId = applicationId
        self.instanceId = instanceId


class PreProcessForm:
    creator: str
    name: str
    projectId: str
    version: str | None
    parent: str | None
    outputURI: str | None
    datasetId: str
    selectedPipelineId: str
    configurationName: str
    isTemplate: bool
    datasetVersion: int | None
    queue: str
    maxIdleTime: str
    instanceId: str
    applicationId: int
    collectionId: str

    def __init__(
        self,
        creator: str,
        name: str,
        projectId: str,
        version: str | None,
        parent: str | None,
        outputURI: str | None,
        datasetId: str | None,
        selectedPipelineId: str,
        configurationName: str,
        isTemplate: bool,
        type: str,
        datasetVersion: int | None,
        queue: str,
        maxIdleTime: str,
        instanceId: str,
        applicationId: int,
        collectionId: str,
    ) -> None:
        self.creator = creator
        self.name = name
        self.projectId = projectId
        self.version = version
        self.parent = parent
        self.outputURI = outputURI
        self.datasetId = datasetId
        self.selectedPipelineId = selectedPipelineId
        self.configurationName = configurationName
        self.isTemplate = isTemplate
        self.datasetVersion = datasetVersion
        self.queue = queue
        self.maxIdleTime = maxIdleTime
        self.instanceId = instanceId
        self.applicationId = applicationId
        self.collectionId = collectionId
