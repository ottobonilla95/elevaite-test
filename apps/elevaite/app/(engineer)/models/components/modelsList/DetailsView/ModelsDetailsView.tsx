"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { useRoles } from "../../../../../lib/contexts/RolesContext";
import { ModelsStatus, type EvaluationObject, type ModelObject } from "../../../../../lib/interfaces";
import { ModelsDetailsHeader } from "./ModelsDetailsHeader";
import { ModelsDetailsInferenceTab } from "./ModelsDetailsInferenceTab";
import { ModelsDetailsLogsTab } from "./ModelsDetailsLogsTab";
import { ModelsDetailsPerformanceTab } from "./ModelsDetailsPerformanceTab";
import "./ModelsDetailsView.scss";



// const PARAMETERS_COLUMN_1 = [
//     { label: "Architectures:", value: "MixtrailForCausalLM" },
//     { label: "Max Position Embeddings:", value: "32678" },
//     { label: "Attention Dropout:", value: "0.0" },
//     { label: "Hidden Act:", value: "Silu" },
//     { label: "Hidden Size:", value: "4096" },
//     { label: "Intermediate Size:", value: "14336" },
//     { label: "Initializer Range:", value: "0.02" },
//     { label: "Model Type:", value: "Mixtrail" },
//     { label: "Num Attention Heads:", value: "32" },
//     { label: "Num Experts per tok:", value: "2" },
//     { label: "Num Hidden Layers:", value: "32" },
//     { label: "Num Key Value Heads:", value: "8" },
//     { label: "Num Local Experts:", value: "8" },
// ];

// const PARAMETERS_COLUMN_2 = [
//     { label: "BOS Token ID:", value: "1" },
//     { label: "EOS Token ID:", value: "2" },
//     { label: "Output Router Logits:", value: "false" },
//     { label: "RMS Norm Eps:", value: "1e-05" },
//     { label: "Rope Theta:", value: "1000000.0" },
//     { label: "Router aux Loss:", value: "0.02" },
//     { label: "Sliding Window:", value: "null" },
//     { label: "Tie Word Embeddings:", value: "false" },
//     { label: "Torch DType:", value: "bfloat16" },
//     { label: "Transformers Version:", value: "4.36.0.dev0" },
//     { label: "User Cache:", value: "true" },
//     { label: "Vocab Size:", value: "32000" },
// ];



enum MODELS_DETAILS_TABS {
    GENERAL = "General",
    PARAMETERS = "Parameters",
    PERFORMANCE = "Performance",
    LOGS = "Logs",
    INFERENCE = "Inference",
};

enum GENERAL_FIELDS_LABELS {
    CREATED_AT = "CREATED AT:",
    MODEL_TASK = "MODEL TASK:",
    RAM_TO_RUN = "RAM TO RUN:",
    RAM_TO_TRAIN = "RAM TO TRAIN:",
    MODEL_URL = "MODEL URL:",
    PROJECT = "PROJECT:",
    DESCRIPTION = "DESCRIPTION:",
};


const ModelsDetailsTabsArray: MODELS_DETAILS_TABS[] = [
    MODELS_DETAILS_TABS.GENERAL,
    MODELS_DETAILS_TABS.PARAMETERS,
    MODELS_DETAILS_TABS.PERFORMANCE,
    MODELS_DETAILS_TABS.LOGS,
    MODELS_DETAILS_TABS.INFERENCE,
];



export function ModelsDetailsView(): JSX.Element {
    const rolesContext = useRoles();
    const modelsContext = useModels();
    const [selectedTab, setSelectedTab] = useState(MODELS_DETAILS_TABS.GENERAL);
    const [evaluations, setEvaluations] = useState<EvaluationObject[]>([]);
    const [generalFields, setGeneralFields] = useState<{label: GENERAL_FIELDS_LABELS, value: string}[]>([]);
    


    useEffect(() => {
        formatGeneralFields(modelsContext.selectedModel);
        if (modelsContext.selectedModel?.status !== ModelsStatus.DEPLOYED && selectedTab === MODELS_DETAILS_TABS.INFERENCE) {
            setSelectedTab(MODELS_DETAILS_TABS.GENERAL);
        }
        if (modelsContext.selectedModel?.status === ModelsStatus.FAILED && selectedTab !== MODELS_DETAILS_TABS.LOGS) {
            setSelectedTab(MODELS_DETAILS_TABS.LOGS);
        }
    }, [modelsContext.selectedModel]);

    useEffect(() => {
        console.log("parameters", modelsContext.selectedModelParameters);
    }, [modelsContext.selectedModelParameters]);


    function formatGeneralFields(model?: ModelObject): void {
        if (!model) {
            setGeneralFields([]);
            return;
        }
        setGeneralFields([
            { label: GENERAL_FIELDS_LABELS.CREATED_AT, value: dayjs(model.created).format("MMM-DD-YYYY, hh:mm A") },
            { label: GENERAL_FIELDS_LABELS.MODEL_TASK, value: model.task ?? "—" },
            { label: GENERAL_FIELDS_LABELS.RAM_TO_RUN, value: model.memory_requirements?.total_size.value_str ?? "Unknown" },
            { label: GENERAL_FIELDS_LABELS.RAM_TO_TRAIN, value: model.memory_requirements?.training_using_adam.value_str ?? "Unknown" },
            { label: GENERAL_FIELDS_LABELS.MODEL_URL, value: model.endpointUrl ?? "No endpoint created" },
            { label: GENERAL_FIELDS_LABELS.PROJECT, value: rolesContext.selectedProject?.name ?? "—" },
            { label: GENERAL_FIELDS_LABELS.DESCRIPTION, value: model.huggingface_repo ?? "—" },
        ]);
    }

    function getIsTabDisabled(tab: MODELS_DETAILS_TABS, modelStatus: ModelsStatus|undefined): boolean {
        if (tab !== MODELS_DETAILS_TABS.GENERAL && tab !== MODELS_DETAILS_TABS.LOGS &&
            (modelStatus === ModelsStatus.REGISTERING || modelStatus === ModelsStatus.FAILED))
            return true;
        
        return false;
    }



    return (
        <div className="models-details-view-container">

            <div className="models-details-view-contents">

                <ModelsDetailsHeader/>

                <div className="tabs-container">
                    {ModelsDetailsTabsArray.map((tab: MODELS_DETAILS_TABS) => 
                        <CommonButton
                            key={tab}
                            className={[
                                "tab-button",
                                selectedTab === tab ? "active" : undefined,
                                tab === MODELS_DETAILS_TABS.INFERENCE && modelsContext.selectedModel?.status !== ModelsStatus.DEPLOYED ? "hidden" : undefined,
                            ].filter(Boolean).join(" ")}                        
                            onClick={() => { setSelectedTab(tab)}}
                            disabled={getIsTabDisabled(tab, modelsContext.selectedModel?.status)}
                        >
                            {tab}
                        </CommonButton>
                    )}
                </div>

                <div className="model-details-tab-contents">

                    {modelsContext.loading.currentModelParameters ?
                        <div className="loading-message">
                            <ElevaiteIcons.SVGSpinner/>
                            <span>Loading...</span>
                        </div>

                        :

                        <>
                        <div className={["model-details-page-contents general", selectedTab === MODELS_DETAILS_TABS.GENERAL ? "visible" : undefined].filter(Boolean).join(" ")}>
                            {generalFields.map(item =>
                                <ModelBit key={item.label} label={item.label} general
                                    value={item.label === GENERAL_FIELDS_LABELS.MODEL_TASK && modelsContext.selectedModel?.task ? modelsContext.selectedModel.task : item.value}
                                />
                            )}
                        </div>
                        <div className={["model-details-page-contents parameters", selectedTab === MODELS_DETAILS_TABS.PARAMETERS ? "visible" : undefined].filter(Boolean).join(" ")}>
                            <div className="model-column">
                                <ModelBit label="Architectures:" value={modelsContext.selectedModelParameters ? modelsContext.selectedModelParameters.architectures.join(", ") : ""} />
                                <ModelBit label="Model Type:" value={modelsContext.selectedModelParameters ? modelsContext.selectedModelParameters.model_type : ""} />
                                {!modelsContext.selectedModelParameters ? undefined :
                                    Object.keys(modelsContext.selectedModelParameters).map(key => {
                                        if (key !== "model_type" && (
                                            typeof modelsContext.selectedModelParameters?.[key] === "string" ||
                                            typeof modelsContext.selectedModelParameters?.[key] === "number" ||
                                            typeof modelsContext.selectedModelParameters?.[key] === "boolean" ||
                                            modelsContext.selectedModelParameters?.[key] === null
                                        ))
                                            return (
                                                <ModelBit
                                                    key={key}
                                                    label={`${key.split("_").join(" ")}:`}
                                                    value={modelsContext.selectedModelParameters[key] as string}
                                                />
                                            )
                                        return null;
                                    })
                                }
                                {/* {PARAMETERS_COLUMN_1.map(item =>
                                    <ModelBit key={item.label} label={item.label} value={item.value} />
                                )} */}
                            </div>
                            {/* <div className="model-column"> */}
                                {/* {PARAMETERS_COLUMN_2.map(item =>
                                    <ModelBit key={item.label} label={item.label} value={item.value} />
                                )} */}
                            {/* </div> */}
                        </div>
                        <div className={["model-details-page-contents", selectedTab === MODELS_DETAILS_TABS.PERFORMANCE ? "visible" : undefined].filter(Boolean).join(" ")}>
                            <ModelsDetailsPerformanceTab evaluations={evaluations} onEvaluationsChange={setEvaluations} />
                        </div>
                        <div className={["model-details-page-contents", selectedTab === MODELS_DETAILS_TABS.LOGS ? "visible" : undefined].filter(Boolean).join(" ")}>
                            <ModelsDetailsLogsTab evaluations={evaluations} />
                        </div>
                        <div className={["model-details-page-contents", selectedTab === MODELS_DETAILS_TABS.INFERENCE ? "visible" : undefined].filter(Boolean).join(" ")}>
                            <ModelsDetailsInferenceTab/>
                        </div>
                        </>
                    }

                </div>

            </div>
        </div>
    );
}



interface ModelBitProps {
    label: string;
    value: string | number | boolean | null;
    general?: boolean;
}

function ModelBit(props: ModelBitProps): JSX.Element {
    return (
        <div className={["model-bit", props.general ? "general" : undefined].filter(Boolean).join(" ")}>
            <span className="label">{props.label}</span>
            <span>{props.value ? props.value.toString() : "null" }</span>
        </div>
    );
}
