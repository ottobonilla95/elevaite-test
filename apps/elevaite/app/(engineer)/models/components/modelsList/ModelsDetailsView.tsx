"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useState } from "react";
import { ModelsDetailsHeader } from "./ModelsDetailsHeader";
import "./ModelsDetailsView.scss";
import { ModelsContext, useModels } from "../../../../lib/contexts/ModelsContext";



const GENERAL_FIELDS = [
    { label: "CREATED AT:", value: "Jul 31 2023 11:45" },
    { label: "UPDATED AT:", value: "Jul 31 2023 11:45" },
    { label: "MODEL TASK:", value: "question-answering" },
    { label: "RAM TO RUN:", value: "24 GB" },
    { label: "RAM TO TRAIN:", value: "80GB" },
    { label: "FRAMEWORK:", value: "PyTorch" },
    { label: "MODEL URL:", value: "s3://suspendise-lorem-dictum/test-data" },
    { label: "USER:", value: "John Doe" },
    { label: "PROJECT:", value: "Elevaite Test Runs" },
    { label: "DESCRIPTION:", value: "Test Data" },
];

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


interface ModelsDetailsViewProps {

}

export function ModelsDetailsView(props: ModelsDetailsViewProps): JSX.Element {
    const modelsContext = useModels();
    const [selectedTab, setSelectedTab] = useState(MODELS_DETAILS_TABS.GENERAL);


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
                                    <ModelBit key={item.label} label={item.label} value={item.value} general />
                                )}
                            </div>
                            <div className={["model-details-page-contents parameters", selectedTab === MODELS_DETAILS_TABS.PARAMETERS ? "visible" : undefined].filter(Boolean).join(" ")}>
                                <div className="model-column">
                                    {PARAMETERS_COLUMN_1.map(item =>
                                        <ModelBit key={item.label} label={item.label} value={item.value} />
                                    )}
                                </div>
                                <div className="model-column">
                                    {PARAMETERS_COLUMN_2.map(item =>
                                        <ModelBit key={item.label} label={item.label} value={item.value} />
                                    )}
                                </div>
                            </div>
                            <div className={["model-details-page-contents", selectedTab === MODELS_DETAILS_TABS.PERFORMANCE ? "visible" : undefined].filter(Boolean).join(" ")}>
                                Performance test
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
