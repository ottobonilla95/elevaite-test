"use client";
import { CommonDialog, CommonFormLabels, CommonInput, CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { createCollection, getCollectionsOfProject } from "../../../../lib/actions/applicationActions";
import { useRoles } from "../../../../lib/contexts/RolesContext";
import { formDataType, type CollectionObject, type S3PreprocessFormDTO } from "../../../../lib/interfaces";
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
}


interface AddInstancePreprocessProps {
    connectionName: string;
    onConnectionNameChange: (value: string) => void;
    formData: S3PreprocessFormDTO;
    onFormChange: (value: string|boolean, field: string, type: formDataType) => void;
}

export function AddInstancePreprocess({formData, ...props}: AddInstancePreprocessProps): JSX.Element {
    const rolesContext = useRoles();
    const [projectsOptions, setProjectsOptions] = useState<CommonSelectOption[]>([]);
    const [datasetOptions, setDatasetOptions] = useState<CommonSelectOption[]>([]);    
    const [versionOptions, setVersionOptions] = useState<CommonSelectOption[]>([]);
    const [collections, setCollections] = useState<CollectionObject[]>([]);
    const [collectionOptions, setCollectionOptions] = useState<CommonSelectOption[]>([]);
    const [isCollectionsLoading, setIsCollectionsLoading] = useState(false);
    const [isCreateCollectionOpen, setIsCreateCollectionOpen] = useState(false);
    const [createCollectionName, setCreateCollectionName] = useState("");

    
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
        setCollectionOptions(collections.map(item => { return {value: item.id, label: item.name}; }));
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
        setVersionOptions(versionList.map(version => { return {value: version.id, label: getVersionLabel(version)}; } ));
        // Select most recent version
        if (versionList.length > 0) handleVersionChange(versionList[0].id);
    }, [formData.datasetId]);


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

    async function requestCreateCollection(projectId: string, collectionName: string): Promise<void> {
        try {
            setIsCollectionsLoading(true);
            const newCollection = await createCollection(projectId, collectionName);
            setCollections(current => [...current, newCollection]);
            props.onFormChange(newCollection.id, fields.collectionId, formDataType.STRING);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
        } finally {
            setIsCollectionsLoading(false);
        }        
    }

    function resetVersionOptions(): void {
        setVersionOptions([]);
        handleVersionChange("");
    }

    function handleStringChange(value: string, field: string): void {
        props.onFormChange(value, field, formDataType.STRING);
    }

    function handleProjectChange(value: string): void {
        props.onFormChange(value, fields.projectId, formDataType.STRING);
        props.onFormChange("", fields.datasetId, formDataType.STRING);

        const selectedProject = rolesContext.projects.find(project => project.id === value);
        if (selectedProject?.datasets) {
            setDatasetOptions(selectedProject.datasets.map(dataset => { return { value: dataset.id, label: dataset.name }; }));
        }
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
        void requestCreateCollection(formData.projectId, createCollectionName);
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
                    onConfirm={handleCreateCollection}
                    onCancel={closeCollectionCreation}
                >
                    <CommonInput
                        onChange={setCreateCollectionName}
                        onKeyDown={handleEnter}
                    />
                </CommonDialog>
            }


            <CommonInput
                label="Pipeline Name"
                required
                initialValue={props.connectionName}
                onChange={props.onConnectionNameChange}
            />



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
                >
                    <CommonSelect
                        options={collectionOptions}
                        controlledValue={formData.collectionId}
                        onSelectedValueChange={handleCollectionChange}
                        onAdd={handleCollectionAdd}
                        addLabel="Create New Collection"
                        isLoading={isCollectionsLoading}
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