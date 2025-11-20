import { CommonButton, CommonCheckbox, CommonFormLabels, CommonInput, ElevaiteIcons, SimpleTextarea } from "@repo/ui/components";
import { ChevronsLeft, ChevronsRight, PenLine } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { type ToolParametersSchema, type ToolNodeData } from "../../../lib/interfaces";
import { getToolIcon } from "../iconUtils";
import "./ToolsConfigPanel.scss";





interface ToolsConfigPanelProps {
    toolNode: ToolNodeData;
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
    isToolEditing: boolean;
    onToolEdit: (intent: boolean) => void;
    onSave: (parameters: ToolParametersSchema) => void;
}


export function ToolsConfigPanel({ toolNode, ...props }: ToolsConfigPanelProps): JSX.Element {
    const [parameters, setParameters] = useState<ToolParametersSchema>();
    const [requiredSet, setRequiredSet] = useState<Set<string>>(new Set());
    const [name, setName] = useState(toolNode.name);
    const [description, setDescription] = useState(toolNode.description ?? "");
    const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(toolNode.description && toolNode.description.length > 200);
    const isSaveAvailable = useMemo(() => canSave(), [name, parameters, requiredSet]);


    useEffect(() => {
        console.log("Passed Tool:", toolNode);
        resetValues();
    }, [toolNode]);



    function resetValues(): void {
        const base = cloneParameters(toolNode.tool.parameters_schema);
        const merged = applyConfigOverrides(base, (toolNode as unknown as { config?: Record<string, unknown> }).config);
        setParameters(merged);

        setRequiredSet(new Set((toolNode.tool.parameters_schema as unknown as ToolParametersSchema).required ?? []));
        setName(toolNode.config?.tool_name ?? toolNode.name);
        const mergedDescription = toolNode.config?.tool_description ?? toolNode.description ?? "";
        setDescription(mergedDescription);
        setIsDescriptionExpanded(mergedDescription.length > 200);
    }


    function cloneParameters(schema: unknown): ToolParametersSchema {
        try {
            const parsed = JSON.parse(JSON.stringify(schema ?? { properties: {}, required: [] })) as unknown;
            if (!parsed || typeof parsed !== "object" || !("properties" in parsed)) {
                return { properties: {}, required: [] };
            }
            return parsed as ToolParametersSchema;
        } catch {
            return { properties: {}, required: [] };
        }
    }

    function applyConfigOverrides(base: ToolParametersSchema, nodeConfig?: Record<string, unknown>): ToolParametersSchema {
        function isPlainObject(v: unknown): v is Record<string, unknown> { return v !== null && typeof v === "object" && !Array.isArray(v) };
        if (!isPlainObject(nodeConfig) || Object.keys(nodeConfig).length === 0) return base;

        const merged = JSON.parse(JSON.stringify(base)) as ToolParametersSchema;

        if (typeof nodeConfig.tool_name === "string") merged.tool_name = nodeConfig.tool_name;
        if (typeof nodeConfig.tool_description === "string") merged.tool_description = nodeConfig.tool_description;
        if (typeof nodeConfig.tool_defaultName === "string") merged.tool_defaultName = nodeConfig.tool_defaultName;

        const parameterMapping = nodeConfig.param_mapping;
        if (parameterMapping && typeof parameterMapping === "object" && !Array.isArray(parameterMapping)) {
            const entries = Object.entries(parameterMapping as Record<string, unknown>);
            if (entries.length > 0) {
                for (const [key, mapped] of entries) {
                    const prop = merged.properties[key];

                    if (typeof mapped === "string" && (mapped.startsWith("response.") || mapped.startsWith("$prev.response."))) {
                        const sliceFrom = mapped.startsWith("$prev.response.") ? "$prev.response.".length : "response.".length;
                        merged.properties[key] = {
                            ...prop,
                            value: mapped.slice(sliceFrom),
                            isUsingResponse: true,
                        };
                    } else {
                        merged.properties[key] = {
                            ...prop,
                            value: typeof mapped === "number" || typeof mapped === "string" ? mapped : String(mapped),
                            isUsingResponse: false,
                        };
                    }
                }
            }
        }

        return merged;
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
                        error: validateParameter(field.type, String(field.value), requiredSet.has(key), value)
                    },
                },
            };
        });
    }



    function validateParameter(type: "integer" | "number" | "string", value: string, required: boolean, isUsingResponse: boolean): string | undefined {
        const trimmedValue = value.trim();
        const effectiveType: "integer" | "number" | "string" = isUsingResponse ? "string" : type;

        // When using response mapping, empty values are allowed (to reference the whole response)
        if (isUsingResponse && trimmedValue === "") return undefined;

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


    function canSave(): boolean {
        if (!name.trim()) return false;
        if (!parameters?.properties) return true;

        for (const [key, param] of Object.entries(parameters.properties)) {
            const error = validateParameter(
                param.type,
                String(param.value ?? ""),
                requiredSet.has(key),
                Boolean(param.isUsingResponse)
            );
            if (error) return false;
        }

        return true;
    };





    function handleEdit(): void {
        props.onToolEdit(true);
    }

    function handleEditCancel(): void {
        resetValues();
        props.onToolEdit(false);
    }

    function handleEditSave(): void {
        props.onToolEdit(false);

        const base = parameters ?? { properties: {}, required: [] };
        const sanitizedProperties: ToolParametersSchema["properties"] = Object.keys(base.properties).reduce((acc, key) => {
            const p = base.properties[key];
            acc[key] = {
                type: p.type,
                ...(p.title ? { title: p.title } : {}),
                ...(p.description ? { description: p.description } : {}),
                ...(p.value !== undefined ? { value: p.value } : {}),
                ...(p.isUsingResponse ? { isUsingResponse: true } : {}),
            };
            return acc;
        }, {});

        const combinedParameters: ToolParametersSchema = {
            ...base,
            properties: sanitizedProperties,
            tool_defaultName: toolNode.tool.name,
            tool_name: name,
            tool_description: description.trim(),
        };
        console.log("Combined Parameters:", combinedParameters);

        props.onSave(combinedParameters);
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
                    {getToolIcon(toolNode.config?.tool_name ?? toolNode.name)}
                </div>

                <div className="header-labels-container">
                    <span className="header-labels-title">
                        {toolNode.config?.tool_name ?? toolNode.name}
                    </span>
                    <span
                        className="header-labels-description"
                        title={toolNode.config?.tool_description ?? toolNode.description ?? ""}
                    >
                        {toolNode.config?.tool_description ?? toolNode.description ?? ""}
                    </span>
                </div>

                <div className="header-controls-container">
                    <CommonButton
                        onClick={handleEdit}
                        noBackground
                        disabled={props.isToolEditing}
                    >
                        <PenLine size={20} />
                    </CommonButton>

                    <div className="header-controls-sidebar-placeholder" />

                </div>

            </div>

            <div className="tools-details-container">
                <div className="tools-details-scroller">

                    <div className="tools-details-content">

                        <div className={["name-and-description-container", props.isToolEditing ? "expanded" : undefined].filter(Boolean).join(" ")}>
                            <CommonInput
                                controlledValue={name}
                                onChange={setName}
                                label="Tool Name"
                                placeholder="Name (Required)"
                                required
                                disabled={!props.isToolEditing}
                            />

                            <CommonFormLabels
                                label="Tool Description"
                                rightSideItem={
                                    <CommonButton onClick={() => { setIsDescriptionExpanded(!isDescriptionExpanded); }} noBackground>
                                        <ElevaiteIcons.SVGZoom type={isDescriptionExpanded ? "out" : "in"} />
                                    </CommonButton>
                                }
                            >
                                <SimpleTextarea
                                    value={description}
                                    onChange={setDescription}
                                    useCommonStyling
                                    wrapperClassName={["tool-description", isDescriptionExpanded ? "expanded" : undefined].filter(Boolean).join(" ")}
                                    disabled={!props.isToolEditing}
                                />
                            </CommonFormLabels>
                        </div>

                        {!parameters || !Object.keys(parameters.properties).length ?

                            <div className={["no-parameters", props.isToolEditing ? "short" : undefined].filter(Boolean).join(" ")}>
                                No parameters found
                            </div>

                            :

                            Object.entries(parameters.properties).map(([key, parameter]) => {
                                return (
                                    <div className="parameter-input-container" key={key}>
                                        <CommonInput
                                            field={key}
                                            label={parameter.title ?? (parameter.description ?? key)}
                                            required={requiredSet.has(key) && !parameter.isUsingResponse}
                                            errorMessage={parameter.isEdited ? parameter.error : undefined}
                                            placeholder={
                                                parameter.isUsingResponse ? "field_name (or leave empty for whole response)"
                                                    : parameter.type === "integer" ? "e.g., 12345"
                                                        : parameter.type === "number" ? "e.g., 123.45"
                                                            : "e.g., Static text"
                                            }
                                            info={`Expected input type:\n${parameter.isUsingResponse ? "string (response variable reference)\nLeave empty to use the entire response" : parameter.type}`}
                                            onChange={(value, field) => { handleParameterChange(field ?? key, value); }}
                                            controlledValue={parameter.value !== undefined ? String(parameter.value) : ""}
                                            disabled={!props.isToolEditing}
                                            emptyValueWhenDisabled="No parameter value defined"
                                        />
                                        <div className={["parameter-input-details", props.isToolEditing ? "editing" : ""].filter(Boolean).join(" ")}>
                                            <div className="result-checkbox"
                                                title={`Link to connected tool's or agent's response.\n\nLeave empty to use the entire response.\nOr specify a field name to use a specific field.\n\nE.g., If the response is {result: "value"},\nuse "result" to access just "value".`}>
                                                <ElevaiteIcons.SVGConnect />
                                                <CommonCheckbox
                                                    checked={Boolean(parameter.isUsingResponse)}
                                                    onChange={(value) => { handleResponseUsageChange(key, value) }}
                                                    disabled={!props.isToolEditing}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                );
                            })
                        }

                    </div>

                </div>

                {!props.isToolEditing ? undefined :

                    <div className="editing-buttons-container">
                        <CommonButton onClick={handleEditCancel} className="tool-button cancel">
                            Cancel
                        </CommonButton>
                        <CommonButton onClick={handleEditSave} className="tool-button" disabled={!isSaveAvailable}>
                            Save
                        </CommonButton>
                    </div>
                }
            </div>


        </div>
    );
}