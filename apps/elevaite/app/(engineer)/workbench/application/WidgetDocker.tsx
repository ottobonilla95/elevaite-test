"use client";
import type { CommonSelectOption } from "@repo/ui/components";
import { useEffect, useState } from "react";
import type { AppInstanceObject, ApplicationObject, PipelineObject, PipelineStep } from "../../../lib/interfaces";
import "./WidgetDocker.scss";
import { ConsoleLogWidget } from "./widgets/ConsoleLogWidget";
import MainDetailsWidget from "./widgets/MainDetailsWidget";
import { PipelineWidget } from "./widgets/PipelineWidget";
import { ProgressTrackingWidget } from "./widgets/ProgressTrackingWidget";



interface WidgetDockerProps {
    applicationId: string | null;
    applicationDetails?: ApplicationObject;
    selectedInstance: AppInstanceObject | undefined;
    selectedFlow?: CommonSelectOption;
    pipelines?: PipelineObject[];
}

export default function WidgetDocker(props: WidgetDockerProps): JSX.Element {
    // const [displayedWidgets, setDisplayedWidgets] = useState<ReactNode>();
    const [selectedPipelineSteps, setSelectedPipelineSteps] = useState<PipelineStep[]>([]);
    const [initialStep, setInitialStep] = useState("");


    // useEffect(() => {
        // setDisplayedWidgets(getConditionalWidgets());
    // }, [props]);

    useEffect(() => {
        if (!props.pipelines || !props.selectedFlow) return;
        const relevantPipeline = props.pipelines.find(item => item.id === props.selectedFlow?.value);
        if (relevantPipeline) {
            setSelectedPipelineSteps(relevantPipeline.steps);
            setInitialStep(relevantPipeline.entry);
        }
    }, [props.pipelines, props.selectedFlow]);


    // function getConditionalWidgets(): ReactNode {
    //     if (!props.applicationDetails) return null;
    //     switch (props.applicationDetails.applicationType) {

    //         case ApplicationType.INGEST: return (
    //             <>
    //                 <ProgressTrackingWidget
    //                     key="progressTracking"
    //                     applicationId={props.applicationId}
    //                     instance={props.selectedInstance}
    //                 />
    //                 <PipelineWidget
    //                     key="pipeline"
    //                     pipelineSteps={selectedPipelineSteps}
    //                     initialStep={initialStep}
    //                     selectedInstance={props.selectedInstance}
    //                 />
    //             </>
    //         );

    //         case ApplicationType.PREPROCESS: return (selectedPipelineSteps.length > 0 ?
    //             <>
    //                 <ProgressTrackingWidget
    //                     key="progressTracking"
    //                     applicationId={props.applicationId}
    //                     instance={props.selectedInstance}
    //                 />
    //                 <PipelineWidget
    //                     key="pipeline"
    //                     flowLabel={props.selectedFlow?.label}
    //                     pipelineSteps={selectedPipelineSteps}
    //                     initialStep={initialStep}
    //                     selectedInstance={props.selectedInstance}
    //                 />
    //             </>
    //         : null);
    //     }
    // }

    return (
        <div className="widget-docker-container">
            <div className="widget-docker-contents">
                {!props.selectedInstance ? null :
                    <>
                        <MainDetailsWidget instance={props.selectedInstance} />
                        <ProgressTrackingWidget
                            applicationId={props.applicationId}
                            instance={props.selectedInstance}
                            type={props.applicationDetails?.applicationType}
                        />
                    </>
                }
                <PipelineWidget
                    type={props.applicationDetails?.applicationType}
                    flowLabel={props.selectedFlow?.label}
                    pipelineSteps={selectedPipelineSteps}
                    initialStep={initialStep}
                    selectedInstance={props.selectedInstance}
                />
                <ConsoleLogWidget instance={props.selectedInstance} />
            </div>
        </div>
    );
}