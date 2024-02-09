"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import utc from 'dayjs/plugin/utc';
import { Fragment, useEffect, useState } from "react";
import { AppInstanceObject, AppInstanceStatus, PipelineStatus, PipelineStatusItem, PipelineStep, PipelineStepData } from "../../../../lib/interfaces";
import "./PreprocessPipelineWidget.scss";

dayjs.extend(utc);



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
    flowLabel?: string;
    pipelineSteps?: PipelineStep[];
    initialStep?: string;
    selectedInstance?: AppInstanceObject;
}

export function PreprocessPipelineWidget(props: PreprocessPipelineWidgetProps): JSX.Element {
    const [isClosed, setIsClosed] = useState(false);
    const [foundationSteps, setFoundationSteps] = useState<(PipelineStep & PipelineStepData)[][]>([]);
    const [displaySteps, setDisplaySteps] = useState<(PipelineStep & PipelineStepData)[][]>([]);


    useEffect(() => {
        formatSteps();
    }, [props.pipelineSteps, props.initialStep]);

    useEffect(() => {
        setDisplaySteps(props.selectedInstance?.pipelineStatuses ? getDisplaySteps(foundationSteps, props.selectedInstance.pipelineStatuses) : foundationSteps);
    }, [foundationSteps, props.selectedInstance]);


    // Arange the received steps into a matrix that can be displayed directly.
    function formatSteps(): void {
        if (!props.pipelineSteps) return;

        const formattedSteps: PipelineStep[][] = [];
        let returnedResults = -1;
        while (returnedResults != 0) {
            const lastIndexResults = formattedSteps.length > 0 ? formattedSteps[formattedSteps.length-1] : [];
            const dependencies = lastIndexResults.map(item => item.id);
            const results = returnStepsWhichDependOn(props.pipelineSteps, dependencies);
            returnedResults = results.length;
            if (results.length > 0) formattedSteps.push(results);
        }
        // const finalizedSteps = getFinalizedSteps(formattedSteps, props.pipelineStatuses);
        setFoundationSteps(formattedSteps);
    }

    // Return array of steps that have any of the dependencies in their own dependsOn array.
    function returnStepsWhichDependOn(steps: PipelineStep[], dependencies: string[]): PipelineStep[] {
        const returningSteps: PipelineStep[] = [];
        for (const step of steps) {
            if ((dependencies.length === 0 && step.dependsOn.length ===0) || 
                step.dependsOn.some(id => { return dependencies.includes(id); })
            ) returningSteps.push(step);
        }
        return returningSteps;
    }


    function getDisplaySteps(steps: PipelineStep[][], statuses?: PipelineStatusItem[]): (PipelineStep & PipelineStepData)[][] {
        const stepClone = JSON.parse(JSON.stringify(steps));
        if (!statuses || statuses.length === 0) return stepClone;

        for (const status of statuses) {
            let relevantStep: (PipelineStep & PipelineStepData) | undefined = undefined;
            for (const stepGroup of stepClone) {
                for (const step of stepGroup) {
                    if (step.id === status.step) relevantStep = step;
                }
            }
            if (relevantStep) {
                relevantStep.startTime = status.startTime;
                relevantStep.endTime = status.endTime;
                relevantStep.status = status.status;
            }
        }
        return stepClone;
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
                        {`Pre-process ${props.flowLabel} Flow`}
                    </div>

                    <div className="flow-scroller">
                        <div className="flow-content">

                        <div className="flow-start">
                            <div className="backdrop"/>
                            <span>Start</span>
                        </div>

                        {displaySteps?.map((stepGroup, index) => 
                        
                            <Fragment key={index}>
                                <ElevaiteIcons.SVGArrowLong/>
                                <div className="step-group-container">
                                    {stepGroup.map(step => 
                                        <StepBlock
                                            key={step.id}
                                            stepNumber={index+1}
                                            {...step}
                                        />
                                    )}
                                </div>
                            </Fragment>
                        )}

                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}




function StepBlock(props: (PipelineStep & PipelineStepData) & { stepNumber?: number; }): JSX.Element {

    function getRelevantIcon(status?: PipelineStatus): React.ReactNode {
        switch (status) {
            case PipelineStatus.IDLE: return <div title="Idle"><ElevaiteIcons.SVGTarget className="step-block-icon starting" size={12}/></div>
            case PipelineStatus.RUNNING: return <div title="Running"><ElevaiteIcons.SVGInstanceProgress className="step-block-icon ongoing" size={12}/></div>
            case PipelineStatus.COMPLETED: return <div title="Completed"><ElevaiteIcons.SVGCheckmark className="step-block-icon completed" size={12}/></div>
            case PipelineStatus.FAILED: return <div title="Failed"><ElevaiteIcons.SVGTarget className="step-block-icon failed" size={12}/></div>
            default: return null;
        }
    }

    function getTimeTooltip(startTime: string, endTime?: string, status?: PipelineStatus): string {
        const formatting = "DD MMM, hh:mm a";
        if (!startTime) return "";
        let tooltip = "Initialized on: " + dayjs(startTime).utc().format(formatting) + " (utc)";
        if (endTime) {
            tooltip += `\n${status === PipelineStatus.FAILED ? "Failed on" : "Completed on"}: ` + dayjs(endTime).utc().format(formatting) + " (utc)";
        }
        return tooltip;
    }

    return (
        <div className="step-block-container">
            <div className="step-block-header">
                {getRelevantIcon(props.status)}
                <span>{props.stepNumber ? `Step ${props.stepNumber}` : ""}</span>
                {!props.startTime ? null :
                    <div className="time-info-wrapper">
                        <div className="time-info" title={getTimeTooltip(props.startTime, props.endTime, props.status)}>
                            <ElevaiteIcons.SVGInfo/>
                        </div>
                    </div>
                }
            </div>
            <span>{props.title}</span>
        </div>
    );
}



