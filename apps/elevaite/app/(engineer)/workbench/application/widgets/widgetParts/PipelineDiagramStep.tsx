"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { getDisplayValueFromStepDetail } from "../../../../../lib/helpers";
import type { AppInstanceObject, ApplicationType, PipelineStep, PipelineStepData } from "../../../../../lib/interfaces";
import { PipelineStatus } from "../../../../../lib/interfaces";
import "./PipelineDiagramStep.scss";



type PipelineDiagramStepProps =
    PipelineStep &
    PipelineStepData &
{
    stepNumber?: number;
    endStep?: number;
    selectedStepId?: string;
    selectedInstance?: AppInstanceObject;
    type?: ApplicationType;
    onSelectedStep?: (step: PipelineStep, stepOrder?: string) => void;
}


export function PipelineDiagramStep({stepNumber, endStep, selectedStepId, onSelectedStep, ...props}: PipelineDiagramStepProps): JSX.Element {
    const [icon, setIcon] = useState(getRelevantIcon());
    const [stepLabel, setStepLabel] = useState("");


    useEffect(() => {
        setIcon(getRelevantIcon(props.status));
        setStepLabel(getStepLabel(stepNumber, endStep));
    }, [props.id, props.status, stepNumber, endStep]);



    function handleClick(): void {
        if (onSelectedStep) onSelectedStep({...props}, stepLabel);
    }



    function getRelevantIcon(status?: PipelineStatus): React.ReactNode {
        switch (status) {
            case PipelineStatus.IDLE:
                return (<div title="Idle">
                        <ElevaiteIcons.SVGTarget className="pipeline-diagram-step-icon starting" size={12} />
                    </div>);
            case PipelineStatus.RUNNING:
                return (<div title="Running">
                        <ElevaiteIcons.SVGInstanceProgress className="pipeline-diagram-step-icon ongoing" size={12} />
                    </div>);
            case PipelineStatus.COMPLETED:
                return (<div title="Completed">
                        <ElevaiteIcons.SVGCheckmark className="pipeline-diagram-step-icon completed" size={12} />
                    </div>);
            case PipelineStatus.FAILED:
                return (<div title="Failed">
                        <ElevaiteIcons.SVGTarget className="pipeline-diagram-step-icon failed" size={12} />
                    </div>);
            default:
                return (<div title="Idle">
                            <ElevaiteIcons.SVGTarget className="pipeline-diagram-step-icon starting" size={12} />
                        </div>);
        }
    }

    function getStepLabel(current?: number, end?: number): string {
        if (current === undefined) return "";
        if (current === 0) return "Start";
        if (current === end) return "End";
        return `Step ${current.toString()}`;
    }

    function getTimeTooltip(startTime: string, endTime?: string, status?: PipelineStatus): string {
        const formatting = "DD MMM, hh:mm a";
        if (!startTime) return "";
        let tooltip = `Initialized on: ${dayjs(startTime).format(formatting)}`;
        if (endTime) {
            tooltip += `\n${status === PipelineStatus.FAILED ? "Failed on" : "Completed on"}: ${dayjs(endTime).format(formatting)}`;
        }
        return tooltip;
    }

    return (
        <CommonButton
            className={[
                "pipeline-diagram-step-container",
                selectedStepId === props.id ? "selected" : undefined,
            ].filter(Boolean).join(" ")}
            overrideClass
            onClick={handleClick}
        >
            <div className="pipeline-diagram-step-header">
                {icon}
                <span>{stepLabel}</span>
                {!props.startTime ? null : (
                    <div className="time-info-wrapper">
                        <div className="time-info" title={getTimeTooltip(props.startTime, props.endTime, props.status)}>
                            <ElevaiteIcons.SVGInfo />
                        </div>
                    </div>
                )}
            </div>
            <span className={props.status === PipelineStatus.COMPLETED ? "completed" : ""}>{props.title}</span>
            {!props.addedInfo ? null : 
                props.addedInfo.map(info => 
                    <div className="pipeline-extra-container" key={info.label}>
                        <div className="pipeline-extra-label">{`${info.label}:`}</div>
                        <div className="pipeline-extra-text">
                            {getDisplayValueFromStepDetail(info, {...props}, props.selectedInstance, props.type)}
                        </div>
                    </div>
                )
            }
        </CommonButton>
    );
}
