import { CommonButton, CommonCheckbox, CommonInput } from "@repo/ui/components";
import { ChevronsLeft, ChevronsRight, PenLine } from "lucide-react";
import { useEffect, useState } from "react";
import { type ToolNodeData } from "../../../lib/interfaces";
import { getToolIcon } from "../iconUtils";
import "./ToolsConfigPanel.scss";



type JSONScalarType = "integer" | "number" | "string";
interface ParameterValueType {
    type: JSONScalarType;
    description?: string;
    value?: number | string;
    error?: string;
    isEdited?: boolean;
    isUsingResponse?: boolean;
}
interface ParametersSchema { properties: Record<string, ParameterValueType>; required?: string[]; }


interface ToolsConfigPanelProps {
    toolNode: ToolNodeData;
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
    isToolEditing: boolean;
    onToolEdit: (intent: boolean) => void;
}


export function ToolsConfigPanel({toolNode, ...props}: ToolsConfigPanelProps): JSX.Element {
    const [parameters, setParameters] = useState<ParametersSchema>();
    const [requiredSet, setRequiredSet] = useState<Set<string>>(new Set());
    const [name, setName] = useState(toolNode.name);
    const [description, setDescription] = useState(toolNode.description ?? "");


    useEffect(() => {
        console.log("Passed Tool:", toolNode);
        resetValues();
    }, [toolNode]);



    function resetValues(): void {
        setParameters(cloneParameters(toolNode.tool.parameters_schema));
        setRequiredSet(new Set((toolNode.tool.parameters_schema as unknown as ParametersSchema).required ?? []));
    }


    function cloneParameters(schema: unknown): ParametersSchema {
        try {
            const parsed = JSON.parse(JSON.stringify(schema ?? { properties: {}, required: [] })) as unknown;
            if (!parsed || typeof parsed !== "object" || !("properties" in parsed)) {
                return { properties: {}, required: [] };
            }
            return parsed as ParametersSchema;
        } catch {
            return { properties: {}, required: [] };
        }
    }


    function handleParameterChange(key: string, value: string): void {
        setParameters((prev) => {
            if (!prev?.properties[key]) return prev;
            const field = prev.properties[key];
            const isRequired = requiredSet.has(key);
            const newParameter = {
                ...field,
                value,
                error: validateParameter(field.type, value, isRequired, Boolean(field.isUsingResponse)),
                // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- Why do we STILL use this thing? 50% of the time it changes the logic and breaks it!
                isEdited: field.isEdited || Boolean(value)
            };
            return {
                ...prev,
                properties: {
                    ...prev.properties,
                    [key]: newParameter,
                },
            };
        });
    }

    function handleResponseUsageChange(key: string, value: boolean): void {
        setParameters((prev) => {
            if (!prev?.properties[key]) return prev;
            const field = prev.properties[key];
            return {
                ...prev,
                properties: {
                    ...prev.properties,
                    [key]: {
                        ...field,
                        isUsingResponse: value,
                        error: validateParameter(field.type, String(field.value), requiredSet.has(key), value) },
                },
            };
        });
    }



    function validateParameter(type: "integer" | "number" | "string", value: string, required: boolean, isUsingResponse: boolean): string | undefined {
        const trimmedValue = value.trim();
        const effectiveType: "integer" | "number" | "string" = isUsingResponse ? "string" : type;

        if (!required && trimmedValue === "") return undefined;
        if (required && trimmedValue === "") return "This field is required.";

        switch (effectiveType) {
            case "string": return undefined;
            case "integer": {
                const numberValue = Number(trimmedValue);
                if (!Number.isFinite(numberValue) || !Number.isInteger(numberValue)) return "Type mismatch";
                return undefined;
            }
            case "number": {
                const numberValue = Number(trimmedValue);
                if (!Number.isFinite(numberValue)) return "Type mismatch";
                return undefined;
            }
            default: return "Type mismatch";
        }
    }


    function handleEdit(): void {
        props.onToolEdit(true);
    }

    function handleEditCancel(): void {
        resetValues();
        props.onToolEdit(false);
    }

    function handleEditSave(): void {
        props.onToolEdit(false);
        console.log("Saving");
    }


    return (
        <div className="tools-config-panel-container">

            <CommonButton
                className="header-controls-sidebar-button"
                onClick={props.toggleSidebar}
                noBackground
            >
                {props.isSidebarOpen ? <ChevronsRight /> : <ChevronsLeft />}
            </CommonButton>

            <div className="tools-header">

                <div className="header-icon-container">
                    {getToolIcon(toolNode.name)}
                </div>

                <div className="header-labels-container">
                    <span className="header-labels-title">{toolNode.name}</span>
                    <span className="header-labels-description" title={toolNode.description}>{toolNode.description}</span>
                </div>

                <div className="header-controls-container">
                    <CommonButton
                        onClick={handleEdit}
                        noBackground
                    >
                        <PenLine size={20} />
                    </CommonButton>

                    <div className="header-controls-sidebar-placeholder"/>

                </div>

            </div>

            <div className="tools-details-container">
                <div className="tools-details-scroller">

                    {!parameters || !Object.keys(parameters.properties).length ?

                        "No parameters"
                        // TODO: Beautify this
                    :
                        <div className="tools-details-content">

                            {/* TODO: name and description */}

                            {Object.entries(parameters.properties).map(([key, parameter]) => {
                                return (
                                    <div className="parameter-input-container" key={key}>
                                        <CommonInput
                                            field={key}
                                            label={parameter.description ?? key}
                                            required={requiredSet.has(key)}
                                            errorMessage={parameter.isEdited ? parameter.error : undefined}
                                            placeholder={
                                                parameter.isUsingResponse ? "response_parameter_name"
                                                : parameter.type === "integer" ? "e.g., 12345"
                                                : parameter.type === "number" ? "e.g., 123.45"
                                                : "Static text"
                                            }
                                            onChange={(value, field) => { handleParameterChange(field ?? key, value); }}
                                            controlledValue={ parameter.value !== undefined ? String(parameter.value) : "" }
                                            disabled={!props.isToolEditing}
                                            emptyValueWhenDisabled="No parameter value defined"
                                        />
                                        <div className={["parameter-input-details", props.isToolEditing ? "editing" : ""].filter(Boolean).join(" ")}>
                                            <div className="parameter-type"
                                                title={parameter.isUsingResponse && parameter.type !== "string" ? "Ignore the parameter type if you're using a response reference." : undefined}>
                                                <span className="type-label">Type: </span>
                                                <span className={["type-value", parameter.isUsingResponse && parameter.type !== "string" ? "crossed" : undefined].filter(Boolean).join(" ")}>
                                                    {parameter.type}
                                                </span>
                                            </div>
                                            <div className="result-checkbox"
                                                title="Using agent response allows you to utilize references to expected results from the response of a previous agent or tool.">
                                                <span className="checkbox-label">
                                                    Use response?
                                                </span>
                                                <CommonCheckbox
                                                    onChange={(value) => { handleResponseUsageChange(key, value) }}
                                                    disabled={!props.isToolEditing}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}

                        </div>
                    }

                </div>

                {!props.isToolEditing ? undefined :
                 
                    <div className="editing-buttons-container">
                        <CommonButton onClick={handleEditCancel} className="tool-button cancel">
                            Cancel
                        </CommonButton>
                        <CommonButton onClick={handleEditSave} className="tool-button">
                            Save
                        </CommonButton>
                    </div>
                }
            </div>


        </div>
    );
}