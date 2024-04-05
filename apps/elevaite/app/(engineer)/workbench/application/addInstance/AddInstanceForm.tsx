"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { CommonButton, CommonCheckbox, CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { createApplicationConfiguration, createApplicationInstance, updateApplicationConfiguration } from "../../../../lib/actions/applicationActions";
import { AppInstanceConfigurationObject, AppInstanceFieldStructure, AppInstanceFormStructure, ApplicationConfigurationDto, Initializers, S3IngestFormDTO, formDataType } from "../../../../lib/interfaces";
import { AppInstanceFieldTypes } from "../../../../lib/interfaces";
import "./AddInstanceForm.scss";
import { Configurations } from "./Configurations";
import { AddInstanceIngest } from "./AddInstanceIngest";




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
    const [formData, setFormData] = useState(props.addInstanceStructure?.initializer);
    const [isConfirmDisabled, setIsConfirmDisabled] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [isConfigNameOpen, setIsConfigNameOpen] = useState(false);
    const [selectedConfigurationId, setSelectedConfigurationId] = useState("");


    useEffect(() => {
        if (props.initialConfig?.raw) {
            setFormData(props.initialConfig.raw);
            setSelectedConfigurationId(props.initialConfig.id);
        }
    }, []);

    useEffect(() => {
        console.log("Formdata changed", formData);
        if (!props.addInstanceStructure || !formData) return;        
        setIsConfirmDisabled(getIsRequiredFieldEmptyInList(formData, props.addInstanceStructure.fields));
    }, [formData]);



    function getIsRequiredFieldEmptyInList(passedFormData: Initializers, fields: AppInstanceFieldStructure[]): boolean {
        for (const item of fields) {
            if ("required" in item && Boolean(item.required) && item.field) {
                if (!passedFormData[item.field]) {
                    setIsConfirmDisabled(true);
                    return true;
                }
            } else if ("type" in item && item.type === AppInstanceFieldTypes.GROUP) {
                if (getIsRequiredFieldEmptyInList(passedFormData, item.fields)) return true;
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
        if (getIsRequiredFieldEmptyInList(formData, props.addInstanceStructure.fields)) return;

        if (updateId) {
            await updateConf(formData, name, updateId);
        } else {
            await createConf(formData, name);
        }
    }

    async function createConf(configData: Initializers, configName: string): Promise<void> {
        if (!props.applicationId) return;

        const dto: ApplicationConfigurationDto = {
            applicationId: props.applicationId,
            name: configName,
            isTemplate: true,
            raw: configData,
        };
        try {
            setIsProcessing(true);
            await createApplicationConfiguration(props.applicationId, dto);
            props.onClose();
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
            setErrorMessage("The configuration could not be saved. Please try again.")
        } finally {
            setIsProcessing(false);
        }
    }

    async function updateConf(configData: Initializers, configName: string, updateId: string): Promise<void> {        
        if (!props.applicationId) return;

        const dto: Omit<ApplicationConfigurationDto, "applicationId"> = {
            name: configName,
            isTemplate: true,
            raw: configData,
        };
        try {
            setIsProcessing(true);
            await updateApplicationConfiguration(props.applicationId, updateId, dto);
            props.onClose();
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

        // Check all required data.
        if (getIsRequiredFieldEmptyInList(formData, props.addInstanceStructure.fields)) return;

        // Commit to server
        try {
            setIsProcessing(true);
            const response = await createApplicationInstance(props.applicationId, formData);
            props.onClose(response.id);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
            setErrorMessage("An error was encountered. Please try again.")
        } finally {
            setIsProcessing(false);
        }
    }


    function mapFields(fields: AppInstanceFieldStructure[]): JSX.Element {
        const components = fields.map((field) => {            
            if ("import" in field || "export" in field) {
                return (
                    <div className="configurations" key="inputOutput">
                        {!field.import ? null :
                        <CommonButton noBackground>
                            <ElevaiteIcons.SVGImport/>
                            {commonLabels.importConf}
                        </CommonButton>}
                        {!field.export ? null:
                        <CommonButton noBackground>
                            <ElevaiteIcons.SVGExport/>
                            {commonLabels.exportConf}
                        </CommonButton>}
                    </div>
                )
            } else if ("testConnection" in field && field.testConnection) {
                return (
                    <div className="configurations test-connection" key="testConnections">
                        <CommonButton noBackground>
                            <ElevaiteIcons.SVGConnect/>
                            {commonLabels.testConnection}
                        </CommonButton>
                    </div>
                )
            } else if ("type" in field) {
                if (field.type === AppInstanceFieldTypes.GROUP) {
                    return (
                        <div className="group-information" key={`group${field.label}`}>
                            <span>Dataset Info</span>
                            {mapFields(field.fields)}
                        </div>
                    )
                } else if (field.type === AppInstanceFieldTypes.CHECKBOX) {
                    let initialCheckbox = false;
                    if (field.field && formData?.[field.field] && typeof formData[field.field] === "boolean") initialCheckbox = formData[field.field] as boolean;
                    return <CommonCheckbox {...field} defaultTrue={initialCheckbox} onChange={handleFormDataBooleanChange} key={field.field} />
                } 
                let initialValue = "";
                if (field.field && formData?.[field.field] && typeof formData[field.field] === "string") initialValue = formData[field.field] as string;
                return <CommonInput {...field} initialValue={initialValue} onChange={handleFormDataChange} key={field.field} />                
            }
            return null;
        })
        return <>{components}</>;
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
                applicationId={props.applicationId}
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
                            formData={formData as S3IngestFormDTO}
                            onFormChange={handleFormDataChange}
                        />
                        :
                        !props.addInstanceStructure ? null :
                        mapFields(props.addInstanceStructure.fields)
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

