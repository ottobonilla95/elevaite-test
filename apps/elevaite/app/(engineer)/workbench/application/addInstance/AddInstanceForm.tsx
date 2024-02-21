"use client";
import type { CommonSelectOption} from "@repo/ui/components";
import { CommonButton, CommonCheckbox, CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { createApplicationInstance } from "../../../../lib/actions";
import type { AppInstanceFieldStructure, AppInstanceFormStructure, Initializers } from "../../../../lib/interfaces";
import { AppInstanceFieldTypes } from "../../../../lib/interfaces";
import "./AddInstanceForm.scss";




const commonLabels = {
    importConf: "Import Configuration",
    exportConf: "Export Configuration",
    testConnection: "Test Connection",
    buttonCancel: "Cancel",
    buttonConfirm: "Launch",
    unknownHandler: "Unknown Handler",
}



interface AddInstanceFormProps {
    applicationId: string | null;
    addInstanceStructure: AppInstanceFormStructure<Initializers> | undefined;
    onClose: (addId?: string) => void;
    selectedFlow?: CommonSelectOption;
}

export function AddInstanceForm(props: AddInstanceFormProps): JSX.Element {
    const [formData, setFormData] = useState(props.addInstanceStructure?.initializer);
    const [isConfirmDisabled, setIsConfirmDisabled] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const session = useSession();


    useEffect(() => {
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

    function handleFormDataChange(value: string, field: string): void {
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
        if ("selectedPipeline" in data) {
            data.selectedPipeline = flow.value;
        }
     }


    function handleClose(): void {
        props.onClose();
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
            setIsProcessing(false);
            props.onClose(response.id);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error:", error);
            setIsProcessing(false);
            setErrorMessage("An error was encountered. Please try again.")
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
                    return <CommonCheckbox {...field} onChange={handleFormDataBooleanChange} key={field.field} />
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
            <div className="details-scroller">
                <div className="details-content">

                    {!props.addInstanceStructure ? null :
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
                            className="details-button launch"
                            disabled={isConfirmDisabled}
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

