"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { createApplicationConfiguration, createApplicationInstance, getApplicationConfigurations, updateApplicationConfiguration } from "../../../../lib/actions/applicationActions";
import { areShallowObjectsEqual } from "../../../../lib/helpers";
import { NEW_DATASET, formDataType, type AppInstanceConfigurationObject, type AppInstanceFormStructure, type ApplicationConfigurationDto, type ApplicationConfigurationObject, type ApplicationDto, type Initializers, type S3IngestFormDTO, type S3PreprocessFormDTO } from "../../../../lib/interfaces";
import "./AddInstanceForm.scss";
import { AddInstanceIngest } from "./AddInstanceIngest";
import { AddInstancePreprocess } from "./AddInstancePreprocess";
import { Configurations } from "./Configurations";



const commonLabels = {
    importConf: "Import Configuration",
    exportConf: "Export Configuration",
    testConnection: "Test Connection",
    buttonCancel: "Cancel",
    buttonSave: "Save Configuration",
    buttonConfirm: "Launch",
    unknownHandler: "Unknown Handler",
}



interface AddInstanceFormProps {
    applicationId: string | null;
    addInstanceStructure: AppInstanceFormStructure<Initializers> | undefined;
    onClose: (addId?: string) => void;
    selectedFlow?: CommonSelectOption;
    initialConfig?: AppInstanceConfigurationObject|undefined;
}

export function AddInstanceForm(props: AddInstanceFormProps): JSX.Element {
    const session = useSession();
    const [instanceName, setInstanceName] = useState("");
    const [connectionName, setConnectionName] = useState("");
    const [formData, setFormData] = useState(props.addInstanceStructure?.initializer);
    const [isConfirmDisabled, setIsConfirmDisabled] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isConfigurationsLoading, setIsConfigurationsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [isConfigNameOpen, setIsConfigNameOpen] = useState(false);
    const [savedConfigurations, setSavedConfigurations] = useState<ApplicationConfigurationObject[]>([]);
    const [selectedConfigurationId, setSelectedConfigurationId] = useState("");


    useEffect(() => {
        if (props.initialConfig?.raw) {
            setFormData(props.initialConfig.raw);
            setSelectedConfigurationId(props.initialConfig.id);
        }
    }, []);

    useEffect(() => {
        void (async () => {
            if (props.applicationId === null) return;
            await fetchConfigurations(props.applicationId);
        })();
    }, [props.applicationId]);

    useEffect(() => {
        if (!props.addInstanceStructure || !formData) return;        
        setIsConfirmDisabled(getIsRequiredFieldEmptyInForm(formData, props.addInstanceStructure.requiredFields));
    }, [formData]);



    async function fetchConfigurations(applicationId: string): Promise<void> {
        try {
            setIsConfigurationsLoading(true);
            const configList = await getApplicationConfigurations(applicationId);
            setSavedConfigurations(configList ? configList : []);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
        } finally {
            setIsConfigurationsLoading(false);
        }
    }

    function getIsRequiredFieldEmptyInForm(passedFormData: Initializers, fields: string[]): boolean {
        for (const field of fields) {
            // Check for optional values (only one of those needs to exist)
            if (field.includes("#")) {
                const subfields = field.split("#");
                let allMissing = true;
                for (const subfield of subfields) {
                    if (passedFormData[subfield]) {
                        allMissing = false;
                        break;
                    }
                }
                if (allMissing) {
                    return true;
                }
            } else if (!passedFormData[field]) {
                return true;
            }
        }
        return false;
    }

    function handleSelectedConfigurationChange(config: Initializers, configurationId: string): void {
        setSelectedConfigurationId(configurationId);
        setFormData(config);
    }

    function handleFormDataChange(value: string|boolean, field: string, type?: formDataType): void {
        switch (type) {
            case formDataType.STRING: if (typeof value === "string") handleFormDataStringChange(value, field); break;
            case formDataType.BOOLEAN: if (typeof value === "boolean") handleFormDataBooleanChange(value, field); break;
            default: if (typeof value === "string") handleFormDataStringChange(value, field);
        }
    }

    function handleFormDataStringChange(value: string, field: string): void {
        setFormData( (currentValues) => {
            if (!currentValues) return;
            return { ...currentValues, [field]: value}
        });
    }

    function handleFormDataBooleanChange(value: boolean, field: string): void {
        setFormData( (currentValues) => {
            if (!currentValues) return;
            return { ...currentValues, [field]: value}
        });
    }

    function handleErrorMessageClick(): void {
        setErrorMessage("");
    }


    function setUser(data: Initializers): void {
        if (session.data?.user?.name) {
            data.creator = session.data.user.name;
        } else data.creator = "Unknown User";
    }

    function setSelectedPipeline(data: Initializers, flow?: CommonSelectOption): void {
        if (!flow?.value) return;
        if ("selectedPipelineId" in data) {
            data.selectedPipelineId = flow.value;
        }
    }

    function setDataset(data: Initializers): void {
        if (!data.datasetId) return;
        if (data.datasetId.includes(NEW_DATASET)) {
            const datasetName = data.datasetId.replace(NEW_DATASET, "");
            data.datasetId = undefined;
            data.datasetName = datasetName;
        } else data.datasetName = undefined;
    }


    function isConfigurationChanged(data: Initializers, configs: ApplicationConfigurationObject[], configId: string): boolean {
        if (!configId) return true;
        const selectedConfig = configs.find(item => item.id === configId);
        if (!selectedConfig) return true;
        const ignoredProperties = ["creator"];
        return !areShallowObjectsEqual(data, selectedConfig.raw, ignoredProperties);
    }


    function handleClose(): void {
        props.onClose();
    }


    function handleSave(): void {
        setIsConfigNameOpen(true);
    }


    async function finalizeSave(name: string, updateId?: string): Promise<void> {
        if (!props.applicationId || !props.addInstanceStructure || !formData) return;

        // Attach user
        setUser(formData);
        // Attach selected pipeline if relevant
        setSelectedPipeline(formData, props.selectedFlow);

        // Check all required data.
        if (getIsRequiredFieldEmptyInForm(formData, props.addInstanceStructure.requiredFields)) return;

        if (updateId) {
            await updateConf(formData, name, updateId);
        } else {
            await createConf(formData, name);
        }
    }

    async function createConf(configData: Initializers, configName: string): Promise<ApplicationConfigurationObject|undefined> {
        if (!props.applicationId) return;

        const dto: ApplicationConfigurationDto = {
            applicationId: props.applicationId,
            name: configName,
            isTemplate: true,
            raw: configData,
        };
        try {
            setIsProcessing(true);
            props.onClose();
            return await createApplicationConfiguration(props.applicationId, dto);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
            setErrorMessage("The configuration could not be saved. Please try again.")
        } finally {
            setIsProcessing(false);
        }
    }

    async function updateConf(configData: Initializers, configName: string, updateId: string): Promise<ApplicationConfigurationObject|undefined> {        
        if (!props.applicationId) return;

        const dto: Omit<ApplicationConfigurationDto, "applicationId"> = {
            name: configName,
            isTemplate: true,
            raw: configData,
        };
        try {
            setIsProcessing(true);
            props.onClose();
            await updateApplicationConfiguration(props.applicationId, updateId, dto);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
            setErrorMessage("The configuration could not be updated. Please try again.")
        } finally {
            setIsProcessing(false);
        }
    }


    async function handleConfirm(): Promise<void> {
        if (!props.applicationId || !props.addInstanceStructure || !formData) return;

        // Attach user
        setUser(formData);
        // Attach selected pipeline if relevant
        setSelectedPipeline(formData, props.selectedFlow);
        // Check if the dataset is existing or new
        setDataset(formData);

        // console.log("Final Form data:", formData);
        // Check all required data.
        if (getIsRequiredFieldEmptyInForm(formData, props.addInstanceStructure.requiredFields)) return;

        const instanceDto: ApplicationDto = {
            creator: formData.creator,
            instanceName,
            configurationId: "",
            projectId: formData.projectId,
            selectedPipelineId: formData.selectedPipelineId
        }

        // Commit to server
        try {
            setIsProcessing(true);
            if (selectedConfigurationId) {
                if (isConfigurationChanged(formData, savedConfigurations, selectedConfigurationId)) {
                    // Offer to update?
                    // SAVE NEW non-template
                    const configName = `CONFIG_${formData.projectId}_${dayjs().toISOString()}`;
                    const newConfig = await createConf(formData, configName);
                    if (newConfig) {
                        instanceDto.configurationId = newConfig.id;
                        const response = await createApplicationInstance(props.applicationId, instanceDto);
                        props.onClose(response.id);
                    }
                } else {
                    // SAVE with config id.
                    instanceDto.configurationId = selectedConfigurationId;
                    const response = await createApplicationInstance(props.applicationId, instanceDto);
                    props.onClose(response.id);
                }
            } else {
                // SAVE NEW non-template
                const configName = `CONFIG_${formData.projectId}_${dayjs().toISOString()}`;
                const newConfig = await createConf(formData, configName);
                if (newConfig) {
                    instanceDto.configurationId = newConfig.id;
                    const response = await createApplicationInstance(props.applicationId, instanceDto);
                    props.onClose(response.id);
                }
            }
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
            setErrorMessage("An error was encountered. Please try again.")
        } finally {
            setIsProcessing(false);
        }
    }



    return (
        <div className="add-instance-form-container">
            {!isProcessing ? null : 
                <div className="processing">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            }
            {!errorMessage ? null : 
                // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions -- This probably can have a better handling
                <div className="error-container" onClick={handleErrorMessageClick}>
                    <span>{errorMessage}</span>
                </div>
            }
            <div className="details-header">
                {props.addInstanceStructure?.icon}
                <span>{props.addInstanceStructure ? props.addInstanceStructure.title : commonLabels.unknownHandler}</span>
                <CommonButton onClick={handleClose} noBackground>
                    <ElevaiteIcons.SVGXmark/>
                </CommonButton>
            </div>
            <Configurations
                isLoading={isConfigurationsLoading}
                savedConfigurations={savedConfigurations}
                isConfigNameOpen={isConfigNameOpen}
                onCancel={() => { setIsConfigNameOpen(false); }}
                onConfirm={finalizeSave}
                onSelectedConfigurationChange={handleSelectedConfigurationChange}
            />
            <div className="details-scroller">
                <div className="details-content" key={selectedConfigurationId}>

                    {!formData ? undefined :
                        props.applicationId === "1" ? 
                        <AddInstanceIngest
                            instanceName={instanceName}
                            onInstanceNameChange={setInstanceName}
                            formData={formData as S3IngestFormDTO}
                            onFormChange={handleFormDataChange}
                        />
                        :
                        props.applicationId === "2" ? 
                        <AddInstancePreprocess
                            connectionName={connectionName}
                            onConnectionNameChange={setConnectionName}
                            formData={formData as S3PreprocessFormDTO}
                            onFormChange={handleFormDataChange}
                        />
                        : undefined
                    }                    

                    <div className="controls-container">
                        <CommonButton
                            className="details-button"
                            onClick={handleClose}
                        >
                            {commonLabels.buttonCancel}
                        </CommonButton>
                        <CommonButton
                            className="details-button config"
                            disabled={isConfirmDisabled}
                            title={!isConfirmDisabled ? "" : "Mandatory fields (*) are missing"}
                            onClick={handleSave}
                        >
                            {commonLabels.buttonSave}
                        </CommonButton>
                        <CommonButton
                            className="details-button launch"
                            disabled={isConfirmDisabled}
                            title={!isConfirmDisabled ? "" : "Mandatory fields (*) are missing"}
                            onClick={handleConfirm}
                        >
                            {commonLabels.buttonConfirm}
                        </CommonButton>
                    </div>

                </div>
            </div>
        </div>
    );
}

