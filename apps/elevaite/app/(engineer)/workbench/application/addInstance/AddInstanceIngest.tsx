"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { AdvancedSelectOption, CommonButton, CommonCheckbox, CommonDialog, CommonFormLabels, CommonInput, CommonSelect, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { getDatasetsOfProject } from "../../../../lib/actions/applicationActions";
import { useRoles } from "../../../../lib/contexts/RolesContext";
import { NEW_DATASET, formDataType, type RbacDatasetObject, type S3IngestFormDTO } from "../../../../lib/interfaces";
import "./AddInstanceIngest.scss";



const fields: Record<keyof S3IngestFormDTO, keyof S3IngestFormDTO> = {
    description: "description",
    type: "type",
    selectedPipelineId: "selectedPipelineId",
    creator: "creator",
    url: "url",
    useEC2: "useEC2",
    roleARN: "roleARN",
    datasetId: "datasetId",
    datasetName: "datasetName",
    projectId: "projectId",
    parent: "parent",
    outputURI: "outputURI"
}



interface AddInstanceIngestProps {
    instanceName: string;
    onInstanceNameChange: (value: string) => void;
    formData: S3IngestFormDTO;
    onFormChange: (value: string|boolean, field: string, type: formDataType) => void;
}

export function AddInstanceIngest({formData, ...props}: AddInstanceIngestProps): JSX.Element {
    const rolesContext = useRoles();
    const [projectsOptions, setProjectsOptions] = useState<CommonSelectOption[]>([]);
    const [datasets, setDatasets] = useState<RbacDatasetObject[]>([]);
    const [newDatasetOptions, setNewDatasetOptions] = useState<CommonSelectOption[]>([]);
    const [isDatasetsLoading, setIsDatasetsLoading] = useState(false);
    const [datasetOptions, setDatasetOptions] = useState<CommonSelectOption[]>([]);
    const [isCreateDatasetOpen, setIsCreateDatasetOpen] = useState(false);
    const [createDatasetName, setCreateDatasetName] = useState("");

    
    useEffect(() => {
        setProjectsOptions(rolesContext.projects.map(project => { 
            return {value: project.id, label: project.name};
        }));
    }, [rolesContext.projects]);

    useEffect(() => {
        handleDatasetChange("");
        datasets.sort((a, b) => dayjs(a.createDate).isBefore(b.createDate) ? 1 : -1);
        // const mainOptions = datasets.map(dataset => { return { value: dataset.id, label: dataset.name }; });
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
        setDatasetOptions([...newDatasetOptions, ...mainOptions]);
    }, [datasets, newDatasetOptions]);


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



    function handleStringChange(value: string, field: string): void {
        props.onFormChange(value, field, formDataType.STRING);
    }
    function handleBooleanChange(value: boolean, field: string): void {
        props.onFormChange(value, field, formDataType.BOOLEAN);
    }
    function handleProjectChange(value: string): void {
        props.onFormChange(value, fields.projectId, formDataType.STRING);
        void fetchDatasetsOfProject(value);
    }

    function handleDatasetChange(value: string): void {
        props.onFormChange(value, fields.datasetId, formDataType.STRING);
    }

    function handleDatasetAdd(): void {
        setIsCreateDatasetOpen(true);
    }

    function closeDatasetCreation(): void {
        setIsCreateDatasetOpen(false);
    }

    function handleEnter(key: string): void {
        if (key === "Enter") handleCreateDataset();
    }

    function handleCreateDataset(): void {
        if (!createDatasetName) return;
        closeDatasetCreation();
        const newDataset: CommonSelectOption = { value: `${NEW_DATASET}${createDatasetName}`, label: createDatasetName, extras: { prefix: { label: "New" } } };
        setNewDatasetOptions(current => {return [newDataset, ...current]; })
        handleDatasetChange(newDataset.value);
        setCreateDatasetName("");
    }



    return (
        <div className="add-instance-ingest-container">

            {!isCreateDatasetOpen ? undefined : 
                <CommonDialog
                    title="Create New Dataset"
                    confirmLabel="Create"
                    onConfirm={handleCreateDataset}
                    onCancel={closeDatasetCreation}
                    disableConfirm={!createDatasetName}
                >
                    <CommonInput
                        onChange={setCreateDatasetName}
                        onKeyDown={handleEnter}
                    />
                </CommonDialog>
            }


            <CommonInput
                label="Instance Name"
                info="This will be the display name of the instance"
                required
                initialValue={props.instanceName}
                onChange={props.onInstanceNameChange}
            />
            <CommonInput
                field={fields.description}
                label="Description"
                info="Instance description"
                initialValue={formData.description}
                onChange={handleStringChange}
            />
            <CommonInput
                field={fields.url}
                label="S3 URL"
                info="The link to the bucket"
                placeholder="s3://training-data-webex/uncompressed/data/"
                required
                initialValue={formData.url}
                onChange={handleStringChange}
            />
            <CommonCheckbox
                field={fields.useEC2}
                label="Use EC2 Instance Role"
                defaultTrue={formData.useEC2}
                onChange={handleBooleanChange}
            />
            <CommonInput
                field={fields.roleARN}
                label="IAM Role ARN"
                required
                initialValue={formData.roleARN}
                onChange={handleStringChange}
            />


            <div className="configurations test-connection" key="testConnections">
                <CommonButton noBackground disabled>
                    <ElevaiteIcons.SVGConnect/>
                    Test Connection
                </CommonButton>
            </div>


            <div className="group-information">
                <span>Output Dataset Information</span>
                
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
                    key={formData.projectId}
                    label="Dataset Name"
                    required
                >
                    <CommonSelect
                        options={datasetOptions}
                        controlledValue={formData.datasetId}
                        onSelectedValueChange={handleDatasetChange}
                        onAdd={handleDatasetAdd}
                        addLabel="Create New Dataset"
                        isLoading={isDatasetsLoading}
                        AdvancedOptionComponent={AdvancedSelectOption}
                    />
                </CommonFormLabels>
                <CommonInput
                    field={fields.parent}
                    label="Dataset Parent"
                    initialValue={formData.parent}
                    onChange={handleStringChange}
                />
                <CommonInput
                    field={fields.outputURI}
                    label="Dataset Output URI"
                    initialValue={formData.outputURI}
                    onChange={handleStringChange}
                />


            </div>


        </div>
    );
}