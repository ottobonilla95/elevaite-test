"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import type { AppInstanceObject, ApplicationObject, PipelineObject, PipelineStep } from "../../../lib/interfaces";
import { ApplicationType } from "../../../lib/interfaces";
import "./WidgetDocker.scss";
import { ConsoleLogWidget } from "./widgets/ConsoleLogWidget";
import MainDetailsWidget from "./widgets/MainDetailsWidget";
import { PreprocessPipelineWidget } from "./widgets/PreprocessPipelineWidget";
import { ProgressTrackingWidget } from "./widgets/ProgressTrackingWidget";



interface WidgetDockerProps {
    applicationId: string | null;
    applicationDetails?: ApplicationObject;
    selectedInstance: AppInstanceObject | undefined;
    selectedFlow?: CommonSelectOption;
    pipelines?: PipelineObject[];
}

export default function WidgetDocker(props: WidgetDockerProps): JSX.Element {
    const [displayedWidgets, setDisplayedWidgets] = useState<ReactNode>();
    const [selectedPipelineSteps, setSelectedPipelineSteps] = useState<PipelineStep[]>([]);
    const [initialStep, setInitialStep] = useState("");


    useEffect(() => {
        setDisplayedWidgets(getConditionalWidgets());
    }, [props]);

    useEffect(() => {
        if (!props.pipelines || !props.selectedFlow) return;
        const relevantPipeline = props.pipelines.find(item => item.id === props.selectedFlow?.value);
        if (relevantPipeline) {
            setSelectedPipelineSteps(relevantPipeline.steps);
            setInitialStep(relevantPipeline.entry);
        }
    }, [props.pipelines, props.selectedFlow]);


    function getConditionalWidgets(): ReactNode {
        if (!props.selectedInstance || !props.applicationDetails) return null;
        switch (props.applicationDetails.applicationType) {

            case ApplicationType.INGEST: return (
                <ProgressTrackingWidget
                    key="progressTracking"
                    applicationId={props.applicationId}
                    instance={props.selectedInstance}
                />
                );

            case ApplicationType.PREPROCESS: return (selectedPipelineSteps.length > 0 ?
                <PreprocessPipelineWidget
                    key="preprocessPipeline"
                    flowLabel={props.selectedFlow?.label}
                    pipelineSteps={selectedPipelineSteps}
                    initialStep={initialStep}
                    selectedInstance={props.selectedInstance}
                />
            : null);
        }
    }

    return (
        <div className="widget-docker-container">
            <div className="widget-docker-contents">
                <MainDetailsWidget instance={props.selectedInstance} />
                {displayedWidgets}
                <ConsoleLogWidget instance={props.selectedInstance} />
            </div>
        </div>
    );
}