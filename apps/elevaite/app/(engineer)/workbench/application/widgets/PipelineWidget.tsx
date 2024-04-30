"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import type { AppInstanceObject, PipelineStatusItem, PipelineStep, PipelineStepData } from "../../../../lib/interfaces";
import { ApplicationType } from "../../../../lib/interfaces";
import "./PipelineWidget.scss";
import { PipelineDiagram } from "./widgetParts/PipelineDiagram";
import { PipelineInfo } from "./widgetParts/PipelineInfo";






interface PipelineWidgetProps {
    type?: ApplicationType;
    flowLabel?: string;
    pipelineSteps?: PipelineStep[];
    initialStep?: string;
    selectedInstance?: AppInstanceObject;
}

export function PipelineWidget(props: PipelineWidgetProps): JSX.Element {
    const [isClosed, setIsClosed] = useState(false);
    const [foundationSteps, setFoundationSteps] = useState<(PipelineStep & PipelineStepData)[][]>([]);
    const [displaySteps, setDisplaySteps] = useState<(PipelineStep & PipelineStepData)[][]>([]);
    const [selectedStep, setSelectedStep] = useState<(PipelineStep & PipelineStepData)|undefined>();
    const [selectedStepOrder, setSelectedStepOrder] = useState("");



    useEffect(() => {
        formatSteps();
    }, [props.pipelineSteps, props.initialStep]);

    useEffect(() => {
        setDisplaySteps(
            props.selectedInstance?.pipelineStepStatuses
                ? getDisplaySteps(foundationSteps, props.selectedInstance.pipelineStepStatuses)
                : foundationSteps
        );
    }, [foundationSteps, props.selectedInstance]);

    // useEffect(() => {
    //     console.log("Selected step", selectedStep);
    // }, [selectedStep]);



    function handleSelectedStep(step: PipelineStep & PipelineStepData, stepOrder?: string): void {
        setSelectedStep(step.id === selectedStep?.id ? undefined : step);
        setSelectedStepOrder(step.id === selectedStep?.id ? "" : stepOrder ?? "");
    }



    // Arange the received steps into a matrix that can be displayed directly.
    function formatSteps(): void {
        if (!props.pipelineSteps) return;

        const formattedSteps: PipelineStep[][] = [];
        let returnedResults = -1;
        while (returnedResults !== 0) {
            const lastIndexResults = formattedSteps.length > 0 ? formattedSteps[formattedSteps.length-1] : [];
            const dependencies = lastIndexResults.map(item => item.id);
            const results = returnStepsWhichDependOn(props.pipelineSteps, dependencies);
            returnedResults = results.length;
            if (results.length > 0) formattedSteps.push(results);
        }
        setFoundationSteps(formattedSteps);
    }

    // Return array of steps that have any of the dependencies in their own dependsOn array.
    function returnStepsWhichDependOn(steps: PipelineStep[], dependencies: string[]): PipelineStep[] {
        const returningSteps: PipelineStep[] = [];
        for (const step of steps) {
            if (
                (dependencies.length === 0 && step.previousStepIds.length === 0) ||
                step.previousStepIds.some((id) => {
                    return dependencies.includes(id);
                })
            )
                returningSteps.push(step);
        }
        return returningSteps;
    }


    function getDisplaySteps(steps: PipelineStep[][], statuses?: PipelineStatusItem[]): (PipelineStep & PipelineStepData)[][] {
        const stepsClone: PipelineStep[][] = JSON.parse(JSON.stringify(steps)) as PipelineStep[][];
        if (!statuses || statuses.length === 0) return stepsClone;

        for (const status of statuses) {
            let relevantStep: (PipelineStep & PipelineStepData) | undefined;
            for (const stepGroup of stepsClone) {
                for (const step of stepGroup) {
                    if (step.id === status.stepId) relevantStep = step;
                }
            }
            if (relevantStep) {
                relevantStep.startTime = status.startTime;
                relevantStep.endTime = status.endTime;
                relevantStep.status = status.status;
            }
        }
        return stepsClone;
    }

    return (
        <div className="preprocess-pipeline-widget-container">
            <div className="pipeline-header">
                <div className="pipeline-titles">
                    <span className="main">
                        {`${props.type === ApplicationType.INGEST ? "AWS S3 Ingest" : props.type === ApplicationType.PREPROCESS ? "Preprocess" : ""} runtime details`}
                    </span>
                    <span className="sub">
                        {`${props.type === ApplicationType.INGEST ? "" : props.type === ApplicationType.PREPROCESS ? "Preprocess" : ""} ${props.flowLabel ? `${props.flowLabel} ` : ""}pipeline`}
                    </span>
                </div>
                <CommonButton
                    className={["pipeline-accordion-button", isClosed ? "closed" : undefined].filter(Boolean).join(" ")}
                    onClick={() => {
                        setIsClosed((currentValue) => !currentValue);
                    }}
                >
                    <ElevaiteIcons.SVGChevron />
                </CommonButton>
            </div>
            <div className={["pipeline-accordion", isClosed ? "closed" : undefined].filter(Boolean).join(" ")}>
                <div className="pipeline-content">
                    <div className="separator" />
                    {/* <div className="flow-type-title">{`Pre-process ${props.flowLabel} Flow`}</div> */}

                    <div className="pipeline-details-container">

                        {props.selectedInstance ? null :
                            <div className="empty-diagram-notification">
                                <span>This is the default pipeline structure.</span><br />
                                <span>Select an instance from the left sidebar to see details.</span>
                            </div>
                        }

                        <PipelineDiagram
                            steps={displaySteps}
                            selectedStepId={selectedStep?.id}
                            onSelectedStep={handleSelectedStep}
                            type={props.type}
                            selectedInstance={props.selectedInstance}
                        />

                        <PipelineInfo
                            selectedInstance={props.selectedInstance}
                            selectedStep={selectedStep}
                            selectedStepOrder={selectedStepOrder}
                            type={props.type}
                        />
                    </div>

                </div>
            </div>
        </div>
    );
}


