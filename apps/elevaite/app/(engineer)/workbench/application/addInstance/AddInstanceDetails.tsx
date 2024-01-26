"use client";
import { CommonButton, CommonCheckbox, CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { AppInstanceFieldStructure, AppInstanceFieldTypes, AppInstanceFormStructure, Initializers } from "../../../../lib/interfaces";
import "./AddInstanceDetails.scss";
import { createApplicationInstance } from "../../../../lib/actions";




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
    onClose: (refresh?: boolean) => void;
}

export function AddInstanceForm(props: AddInstanceFormProps): JSX.Element {
    const [formData, setFormData] = useState(props.addInstanceStructure?.initializer);
    const [isConfirmDisabled, setIsConfirmDisabled] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);


    useEffect(() => {
        if (!props.addInstanceStructure || !formData) return;        
        setIsConfirmDisabled(getIsRequiredFieldEmptyInList(formData, props.addInstanceStructure.fields));
    }, [formData]);



    function getIsRequiredFieldEmptyInList(formData: Initializers, fields: AppInstanceFieldStructure[]): boolean {
        for (const item of fields) {
            if ("required" in item && !!item.required && item.field) {
                if (!formData[item.field]) {
                    setIsConfirmDisabled(true);
                    return true;
                }
            } else if ("type" in item && item.type === AppInstanceFieldTypes.GROUP) {
                if (getIsRequiredFieldEmptyInList(formData, item.fields)) return true;
            }
        }
        return false;
    }

    function handleFormDataChange(value: string, field: string) {
        setFormData( (currentValues) => {
            if (!currentValues) return;
            return { ...currentValues, [field]: value}
        });
     }

     function handleFormDataBooleanChange(value: boolean, field: string) {
        setFormData( (currentValues) => {
            if (!currentValues) return;
            return { ...currentValues, [field]: value}
        });
     }


    function handleClose(): void {
        props.onClose();
    }


    async function handleConfirm(): Promise<void> {
        if (!props.applicationId || !props.addInstanceStructure || !formData) return;
        // Check all data first.
        if (getIsRequiredFieldEmptyInList(formData, props.addInstanceStructure.fields)) return;

        try {
            console.log("Form data passed:", formData);
            await createApplicationInstance(props.applicationId, formData);
            props.onClose(true);
        } catch (error) {
            console.log("Error:", error);
            props.onClose();
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
                            <span>{"Dataset Info"}</span>
                            {mapFields(field.fields)}
                        </div>
                    )
                } else if (field.type === AppInstanceFieldTypes.CHECKBOX) {
                    return <CommonCheckbox {...field} onChange={handleFormDataBooleanChange} key={field.field} />
                } else {
                    return <CommonInput {...field} onChange={handleFormDataChange} key={field.field} />
                }
            }
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

