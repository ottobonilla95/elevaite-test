"use client";
import { Fragment, useState } from "react";
import "./PreprocessPipelineWidget.scss";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { AppInstanceStatus } from "../../../../lib/interfaces";



const testFlow = [
    {
        step: "Step 1",
        label: "Dataset ID URL",
        status: AppInstanceStatus.COMPLETED,
    },
    {
        step: "Step 2",
        label: "Extract Elements",
        status: AppInstanceStatus.COMPLETED,
    },
    {
        step: "Step 3",
        label: "Chunk Content",
        status: AppInstanceStatus.RUNNING,
    },
    {
        step: "Step 4",
        label: "Approve",
        status: AppInstanceStatus.STARTING,
    },
]




interface PreprocessPipelineWidgetProps {
    selectedFlow?: string;
}

export function PreprocessPipelineWidget(props: PreprocessPipelineWidgetProps): JSX.Element {
    const [isClosed, setIsClosed] = useState(false);

    function getFlowLabel(flow?: string): string {
        switch(flow) {
            case "documents": return "Documents";
            case "threads": return "Threads";
            case "chatChannels": return "Chat Channels";
            case "forums": return "Forums";
            default: return "Documents";
        }
    }
    
    
    return (
        <div className="preprocess-pipeline-widget-container">
            <div className="pipeline-header">
                <span>Preprocess Pipeline</span>
                <CommonButton 
                    className={[
                        "pipeline-accordion-button",
                        isClosed ? "closed" : undefined,
                    ].filter(Boolean).join(" ")}
                    onClick={() => { setIsClosed((currentValue) => !currentValue); }}
                >
                    <ElevaiteIcons.SVGChevron />
                </CommonButton>
            </div>
            <div className={[
                "pipeline-accordion",
                isClosed ? "closed" : undefined,
            ].filter(Boolean).join(" ")}>
                <div className="pipeline-content">

                    <div className="separator"/>
                    <div className="flow-type-title">
                        {`Pre-process ${getFlowLabel(props.selectedFlow)} Flow`}
                    </div>

                    <div className="flow-scroller">
                        <div className="flow-content">

                        <div className="flow-start">
                            <div className="backdrop"/>
                            <span>Start</span>
                        </div>

                        {testFlow.map(item => 
                            <Fragment key={item.step}>
                                <ElevaiteIcons.SVGArrowLong/>
                                <StepBlock {...item}/>
                            </Fragment>
                        )}                        

                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}




function StepBlock(props: {step: string, label: string, status: AppInstanceStatus}): JSX.Element {

    function getRelevantIcon(status: AppInstanceStatus): JSX.Element {
        switch (props.status) {
            case AppInstanceStatus.STARTING: return <ElevaiteIcons.SVGTarget className="step-block-icon starting" size={12}/>
            case AppInstanceStatus.RUNNING: return <ElevaiteIcons.SVGInstanceProgress className="step-block-icon ongoing" size={12}/>
            case AppInstanceStatus.COMPLETED: return <ElevaiteIcons.SVGCheckmark className="step-block-icon completed" size={12}/>
            case AppInstanceStatus.FAILED: return <ElevaiteIcons.SVGTarget className="step-block-icon failed" size={12}/>
        }
    }

    return (
        <div className="step-block-container">
            <div className="step-block-header">
                {getRelevantIcon(props.status)}
                <span>{props.step}</span>
            </div>
            <span>{props.label}</span>
        </div>
    );
}



