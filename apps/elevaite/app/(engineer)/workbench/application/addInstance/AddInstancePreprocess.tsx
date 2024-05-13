"use client";
import { AdvancedSelectOption, CommonDialog, CommonFormLabels, CommonInput, CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { createCollection, getCollectionsOfProject, getDatasetsOfProject } from "../../../../lib/actions/applicationActions";
import { getModelEndpoints, getModels } from "../../../../lib/actions/modelActions";
import { useRoles } from "../../../../lib/contexts/RolesContext";
import { getIsPositiveIntegerOrZero } from "../../../../lib/helpers";
import { EmbeddingModelType, ModelsStatus, formDataType, type CollectionObject, type ModelObject, type RbacDatasetObject, type S3PreprocessFormDTO, type S3PreprocessFormEmbeddingInfo } from "../../../../lib/interfaces";
import "./AddInstancePreprocess.scss";



const fields: Record<keyof S3PreprocessFormDTO, keyof S3PreprocessFormDTO> = {
    type: "type",
    selectedPipelineId: "selectedPipelineId",
    creator: "creator",
    datasetId: "datasetId",
    datasetName: "datasetName",
    projectId: "projectId",
    parent: "parent",
    datasetVersion: "datasetVersion",
    collectionId: "collectionId",
    queue: "queue",
    maxIdleTime: "maxIdleTime",
    embedding_info: "embedding_info",
}


interface AddInstancePreprocessProps {
    connectionName: string;
    onConnectionNameChange: (value: string) => void;
    formData: S3PreprocessFormDTO;
    onFormChange: (value: string|boolean, field: string, type: formDataType) => void;
    onEmbeddingInfoChange: (info: S3PreprocessFormEmbeddingInfo|undefined) => void;
}

export function AddInstancePreprocess({formData, ...props}: AddInstancePreprocessProps): JSX.Element {
    const rolesContext = useRoles();
    const [projectsOptions, setProjectsOptions] = useState<CommonSelectOption[]>([]);
    const [datasets, setDatasets] = useState<RbacDatasetObject[]>([]);
    const [isDatasetsLoading, setIsDatasetsLoading] = useState(false);
    const [datasetOptions, setDatasetOptions] = useState<CommonSelectOption[]>([]);    
    const [versionOptions, setVersionOptions] = useState<CommonSelectOption[]>([]);
    const [collections, setCollections] = useState<CollectionObject[]>([]);
    const [collectionOptions, setCollectionOptions] = useState<CommonSelectOption[]>([]);
    const [isCollectionsLoading, setIsCollectionsLoading] = useState(false);
    const [isCreateCollectionOpen, setIsCreateCollectionOpen] = useState(false);
    const [createCollectionName, setCreateCollectionName] = useState("");
    const [createCollectionDimensions, setCreateCollectionDimensions] = useState("");
    const [models, setModels] = useState<ModelObject[]>([]);
    const [embeddingModelOptions, setEmbeddingModelOptions] = useState<CommonSelectOption[]>([]);
    const [loading, setLoading] = useState(false);



    useEffect(() => {
        void fetchModels();
    }, []);
    
    useEffect(() => {
        setProjectsOptions(rolesContext.projects.map(project => { 
            return {value: project.id, label: project.name};
        }));
    }, [rolesContext.projects]);

    useEffect(() => {
        if (formData.projectId) {
            void fetchCollectionsOfProject(formData.projectId);
        } else {
            setCollections([]);
        }
    }, [formData.projectId]);

    useEffect(() => {
        setCollectionOptions(collections.map(item => { return {
            value: item.id,
            label: item.name,
            extras: {
                postfix: { label: item.size.toString(), tooltip: "Dimensions" }
            }
        };}));
    }, [collections]);

    useEffect(() => {
        // Find versions
        if (!formData.projectId || !formData.datasetId) {resetVersionOptions(); return; }
        const selectedProject = rolesContext.projects.find(project => project.id === formData.projectId);
        if (!selectedProject) {resetVersionOptions(); return; }
        const selectedDataset = selectedProject.datasets.find(dataset => dataset.id === formData.datasetId);
        if (!selectedDataset) {resetVersionOptions(); return; }
        const versionList = selectedDataset.versions;
        // Sort versions
        versionList.sort((a,b) => a.version.toString().localeCompare(b.version.toString()));
        setVersionOptions(versionList.map(version => { return {value: version.version.toString(), label: getVersionLabel(version)}; } ));
        // Select most recent version
        if (versionList.length > 0) handleVersionChange(versionList[0].id);
    }, [formData.datasetId]);


    useEffect(() => {
        handleDatasetChange("");
        datasets.sort((a, b) => dayjs(a.createDate).isBefore(b.createDate) ? 1 : -1);
        const mainOptions: CommonSelectOption[] = datasets.map(dataset => { return { 
            value: dataset.id,
            label: dataset.name,
            extras: {
                postfix: {
                    label: dayjs(dataset.updateDate ?? dataset.createDate).format("DD-MMM-YYYY, hh:mm a"),
                    tooltip: dataset.updateDate ? "Latest update date" : "Creation date"
                },
            }
        }; });
        setDatasetOptions(mainOptions);
    }, [datasets]);



    async function fetchCollectionsOfProject(projectId: string): Promise<void> {
        try {
            setIsCollectionsLoading(true);
            const collectionsList = await getCollectionsOfProject(projectId);
            
            setCollections(collectionsList ? collectionsList : []);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
        } finally {
            setIsCollectionsLoading(false);
        }
    }

    async function requestCreateCollection(projectId: string, collectionName: string, collectionDimensions: string): Promise<void> {
        if (!getIsPositiveIntegerOrZero(collectionDimensions)) return;
        try {
            setIsCollectionsLoading(true);
            const newCollection = await createCollection(projectId, collectionName, collectionDimensions);
            setCollections(current => [...current, newCollection]);
            props.onFormChange(newCollection.id, fields.collectionId, formDataType.STRING);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
        } finally {
            setIsCollectionsLoading(false);
            closeCollectionCreation();
        }        
    }

    async function fetchModels(): Promise<void> {
        try {
            setLoading(true);
            const fetchedModels = await getModels();
            const modelEndpoints = await getModelEndpoints();
            const adjustedModels = fetchedModels.map(model => {
                const foundEndpoint = modelEndpoints.find(endpoint => endpoint.model_id === model.id);
                if (foundEndpoint) {
                    return {...model, status: ModelsStatus.DEPLOYED, endpointUrl: foundEndpoint.url, endpointId: foundEndpoint.endpoint_id.toString()};
                }
                return model;
            });
            setModels(adjustedModels);
            const options: CommonSelectOption[] = [
                {
                    value: "default",
                    label: "text-embedding-ada-002 | OpenAI",
                }
            ];
            for (const model of adjustedModels) {
                if (model.status === ModelsStatus.DEPLOYED && model.task === "sentence-similarity") options.push({
                    value: model.id.toString(), label: `${model.name} | Local`
                })
            }
            setEmbeddingModelOptions(options);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching models:", error);
        } finally {
            setLoading(false);
        }
    }


    async function fetchDatasetsOfProject(projectId: string): Promise<void> {
        try {
            setIsDatasetsLoading(true);
            const fetchedDatasets = await getDatasetsOfProject(projectId);
            setDatasets(fetchedDatasets);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
        } finally {
            setIsDatasetsLoading(false);
        }
    }
    

    function handleEmbeddingModelChange(value: string): void {
        const selectedModel = models.find(item => item.id.toString() === value);
        if (!selectedModel){
            props.onEmbeddingInfoChange(undefined);
            return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_MODELS_API_URL;
        props.onEmbeddingInfoChange({
            name: selectedModel.name,
            type: EmbeddingModelType.LOCAL,
            dimensions: "0",
            inference_url: selectedModel.endpointUrl && baseUrl ? `${baseUrl}${selectedModel.endpointUrl}` : undefined,
        });
    }


    ////////// DEMO DATA


    const vectorDBOptions: CommonSelectOption[] = [
        {value: "Qdrant"},
        {value: "Elasticsearch v8.13", disabled: true},
        {value: "Weaviate", disabled: true},
        {value: "Faiss", disabled: true},
        {value: "MongoDB Atlas", disabled: true},
    ];

    function handleEmptyChange(): void {
        // We shouldn't do anything here (for now?)
    }

    //^^^^^^^^^^^^^^^ DEMO DATA 



    function resetVersionOptions(): void {
        setVersionOptions([]);
        handleVersionChange("");
    }

    function handleStringChange(value: string, field: string): void {
        props.onFormChange(value, field, formDataType.STRING);
    }

    function handleProjectChange(value: string): void {
        props.onFormChange(value, fields.projectId, formDataType.STRING);
        void fetchDatasetsOfProject(value);
    }

    function handleDatasetChange(value: string): void {
        props.onFormChange(value, fields.datasetId, formDataType.STRING);
    }

    function handleVersionChange(value: string): void {
        props.onFormChange(value, fields.datasetVersion, formDataType.STRING);
    }

    function handleCollectionChange(value: string): void {
        props.onFormChange(value, fields.collectionId, formDataType.STRING);
    }

    function handleCollectionAdd(): void {
        setIsCreateCollectionOpen(true);
    }

    function closeCollectionCreation(): void {
        setIsCreateCollectionOpen(false);
    }

    function handleEnter(key: string): void {
        if (key === "Enter") handleCreateCollection();
    }

    function handleCreateCollection(): void {
        if (!formData.projectId || !createCollectionName) return;
        void requestCreateCollection(formData.projectId, createCollectionName, createCollectionDimensions);
    }


    function getVersionLabel(version: {id: string; commitId: string; version: string|number; createDate: string;}): string {
        return `${version.version.toString()} - ${dayjs(version.createDate).format("MMM-DD-YYYY, hh:mm a")}`;
    }

    
    
    return (
        <div className="add-instance-preprocess-container">

            {!isCreateCollectionOpen ? undefined : 
                <CommonDialog
                    title="Create New Collection"
                    confirmLabel="Create"
                    disableConfirm={isCollectionsLoading || !createCollectionName || !getIsPositiveIntegerOrZero(createCollectionDimensions)}
                    onConfirm={handleCreateCollection}
                    onCancel={closeCollectionCreation}
                >
                    <CommonFormLabels
                        label="Collection Name"
                        required
                    >
                        <CommonInput
                            onChange={setCreateCollectionName}
                            onKeyDown={handleEnter}
                        />
                    </CommonFormLabels>
                    <CommonFormLabels
                        label="Dimensions"
                        required
                        errorMessage={!createCollectionDimensions || getIsPositiveIntegerOrZero(createCollectionDimensions) ? "" : "Positive integer or 0"}
                    >
                        <CommonInput
                            onChange={setCreateCollectionDimensions}
                            onKeyDown={handleEnter}
                        />
                    </CommonFormLabels>
                </CommonDialog>
            }


            <CommonInput
                label="Pipeline Name"
                // required
                initialValue={props.connectionName}
                onChange={props.onConnectionNameChange}
            />

            <CommonFormLabels
                label="Embedding Model"
                required
            >
                <CommonSelect
                    options={embeddingModelOptions}
                    defaultValue="default"
                    onSelectedValueChange={handleEmbeddingModelChange}
                    isLoading={loading}
                    noDoubleClick
                />
            </CommonFormLabels>


            <div className="group-information">
                <span>Input Dataset</span>
                
                <CommonFormLabels
                    label="Dataset Project"
                    required
                >
                    <CommonSelect
                        options={projectsOptions}
                        defaultValue={projectsOptions.find(item => item.label === "Default Project")?.value}
                        callbackOnDefaultValue
                        onSelectedValueChange={handleProjectChange}
                        isLoading={rolesContext.loading.projects}
                    />
                </CommonFormLabels>
                <CommonFormLabels
                    label="Dataset Name"
                    required
                >
                    <CommonSelect
                        options={datasetOptions}
                        controlledValue={formData.datasetId}
                        onSelectedValueChange={handleDatasetChange}
                        isLoading={isDatasetsLoading}
                        AdvancedOptionComponent={AdvancedSelectOption}
                    />
                </CommonFormLabels>
                <CommonFormLabels
                    label="Dataset Version"
                >
                    <CommonSelect
                        options={versionOptions}
                        controlledValue={formData.datasetVersion}
                        onSelectedValueChange={handleVersionChange}
                    />
                </CommonFormLabels>

            </div>



            <div className="group-information">
                <span>Output Dataset</span>

                <CommonFormLabels
                    label="Collection"
                    required
                >
                    <CommonSelect
                        options={collectionOptions}
                        controlledValue={formData.collectionId}
                        onSelectedValueChange={handleCollectionChange}
                        onAdd={handleCollectionAdd}
                        addLabel="Create New Collection"
                        isLoading={isCollectionsLoading}
                        AdvancedOptionComponent={AdvancedSelectOption}
                    />
                </CommonFormLabels>

                <CommonFormLabels
                    label="Vector DB"
                    required
                >
                    <CommonSelect
                        options={vectorDBOptions}
                        defaultValue={vectorDBOptions[0]?.value}
                        onSelectedValueChange={handleEmptyChange}
                    />
                </CommonFormLabels>

            </div>



            <CommonInput
                field={fields.queue}
                label="Queue"
                initialValue={formData.queue}
                onChange={handleStringChange}
                disabled
            />
            <CommonInput
                field={fields.maxIdleTime}
                label="Maximum Idle Time"
                initialValue={formData.maxIdleTime}
                onChange={handleStringChange}
                disabled
            />


        </div>
    );
}