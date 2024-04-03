"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useSession } from "next-auth/react";
import { useState } from "react";
import { useModels } from "../../../../lib/contexts/ModelsContext";
import { ModelsStatus } from "../../../../lib/interfaces";
import { ModelsDetailsHeader } from "./ModelsDetailsHeader";
import { ModelsDetailsPerformance } from "./ModelsDetailsPerformance";
import "./ModelsDetailsView.scss";



const PARAMETERS_COLUMN_1 = [
    { label: "Architectures:", value: "MixtrailForCausalLM" },
    { label: "Max Position Embeddings:", value: "32678" },
    { label: "Attention Dropout:", value: "0.0" },
    { label: "Hidden Act:", value: "Silu" },
    { label: "Hidden Size:", value: "4096" },
    { label: "Intermediate Size:", value: "14336" },
    { label: "Initializer Range:", value: "0.02" },
    { label: "Model Type:", value: "Mixtrail" },
    { label: "Num Attention Heads:", value: "32" },
    { label: "Num Experts per tok:", value: "2" },
    { label: "Num Hidden Layers:", value: "32" },
    { label: "Num Key Value Heads:", value: "8" },
    { label: "Num Local Experts:", value: "8" },
];

const PARAMETERS_COLUMN_2 = [
    { label: "BOS Token ID:", value: "1" },
    { label: "EOS Token ID:", value: "2" },
    { label: "Output Router Logits:", value: "false" },
    { label: "RMS Norm Eps:", value: "1e-05" },
    { label: "Rope Theta:", value: "1000000.0" },
    { label: "Router aux Loss:", value: "0.02" },
    { label: "Sliding Window:", value: "null" },
    { label: "Tie Word Embeddings:", value: "false" },
    { label: "Torch DType:", value: "bfloat16" },
    { label: "Transformers Version:", value: "4.36.0.dev0" },
    { label: "User Cache:", value: "true" },
    { label: "Vocab Size:", value: "32000" },
];



enum MODELS_DETAILS_TABS {
    GENERAL = "General",
    PARAMETERS = "Parameters",
    PERFORMANCE = "Performance",
};


const ModelsDetailsTabsArray: MODELS_DETAILS_TABS[] = [
    MODELS_DETAILS_TABS.GENERAL,
    MODELS_DETAILS_TABS.PARAMETERS,
    MODELS_DETAILS_TABS.PERFORMANCE,
];



export function ModelsDetailsView(): JSX.Element {
    const session = useSession();
    const modelsContext = useModels();
    const [selectedTab, setSelectedTab] = useState(MODELS_DETAILS_TABS.GENERAL);

    

    const GENERAL_FIELDS = [
        { label: "CREATED AT:", value: dayjs().format("MMM-DD-YYYY, hh:mm A") },
        { label: "UPDATED AT:", value: dayjs().format("MMM-DD-YYYY, hh:mm A") },
        { label: "MODEL TASK:", value: "question-answering" },
        { label: "RAM TO RUN:", value: "24 GB" },
        { label: "RAM TO TRAIN:", value: "80 GB" },
        { label: "FRAMEWORK:", value: "PyTorch" },
        { label: "MODEL URL:", value: "s3://suspendise-lorem-dictum/test-data" },
        { label: "USER:", value: session.data?.user?.name ? session.data.user.name : "Unknown User" },
        { label: "PROJECT:", value: "Elevaite Test Runs" },
        { label: "DESCRIPTION:", value: "Test Data" },
    ];

    return (
        <div className="models-details-view-container">

            <div className="models-details-view-contents">

                <ModelsDetailsHeader/>

                <div className="tabs-container">
                    {ModelsDetailsTabsArray.map((item: MODELS_DETAILS_TABS) => 
                        <CommonButton
                            key={item}
                            className={[
                                "tab-button",
                                selectedTab === item ? "active" : undefined,
                            ].filter(Boolean).join(" ")}                        
                            onClick={() => { setSelectedTab(item)}}
                            disabled={item !== MODELS_DETAILS_TABS.GENERAL &&
                                (modelsContext.selectedModel?.status === ModelsStatus.REGISTERING || modelsContext.selectedModel?.status === ModelsStatus.FAILED)}
                        >
                            {item}
                        </CommonButton>
                    )}
                </div>

                <div className="models-details-scroller">

                    <div className="model-details-tab-contents">

                        {modelsContext.loading.currentModelParameters ?
                            <div className="loading-message">
                                <ElevaiteIcons.SVGSpinner/>
                                <span>Loading...</span>
                            </div>

                            :

                            <>
                            <div className={["model-details-page-contents general", selectedTab === MODELS_DETAILS_TABS.GENERAL ? "visible" : undefined].filter(Boolean).join(" ")}>
                                {GENERAL_FIELDS.map(item =>
                                    <ModelBit key={item.label} label={item.label} general
                                        value={item.label === "MODEL TASK:" && modelsContext.selectedModel?.task ? modelsContext.selectedModel.task : item.value}
                                    />
                                )}
                            </div>
                            <div className={["model-details-page-contents parameters", selectedTab === MODELS_DETAILS_TABS.PARAMETERS ? "visible" : undefined].filter(Boolean).join(" ")}>
                                <div className="model-column">
                                    <ModelBit label="Architectures" value={modelsContext.selectedModelParameters ? modelsContext.selectedModelParameters.architectures.join(", ") : ""} />
                                    <ModelBit label="Model Type" value={modelsContext.selectedModelParameters ? modelsContext.selectedModelParameters.model_type : ""} />
                                    {!modelsContext.selectedModelParameters ? undefined :
                                        Object.keys(modelsContext.selectedModelParameters).map(key => {
                                            if (typeof modelsContext.selectedModelParameters?.[key] === "string")
                                                return (
                                                    <ModelBit
                                                        key={key}
                                                        label={key.split("_").join(" ")}
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
                                <ModelsDetailsPerformance/>
                            </div>
                            </>
                        }

                    </div>

                </div>

            </div>
        </div>
    );
}



interface ModelBitProps {
    label: string;
    value: string;
    general?: boolean;
}

function ModelBit(props: ModelBitProps): JSX.Element {
    return (
        <div className={["model-bit", props.general ? "general" : undefined].filter(Boolean).join(" ")}>
            <span>{props.label}</span>
            <span>{props.value}</span>
        </div>
    );
}
