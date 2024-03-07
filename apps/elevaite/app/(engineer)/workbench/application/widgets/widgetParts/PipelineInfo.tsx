"use client";
import type { AppInstanceObject, ApplicationType, PipelineStep, PipelineStepData } from "../../../../../lib/interfaces";
import { PipelineDataLake } from "./PipelineDataLake";
import "./PipelineInfo.scss";
import { PipelineInfoConfiguration } from "./PipelineInfoConfiguration";
import { PipelineInfoDetails } from "./PipelineInfoDetails";
import { PipelineInfoHeader } from "./PipelineInfoHeader";
import { PipelineInfoStatus } from "./PipelineInfoStatus";
import { PipelineWebhook } from "./PipelineWebhook";



interface PipelineInfoProps {
    selectedInstance?: AppInstanceObject;
    selectedStep?: PipelineStep & PipelineStepData;
    selectedStepOrder?: string;
    type?: ApplicationType;
}

export function PipelineInfo(props: PipelineInfoProps): JSX.Element {

    return (
        <div className="pipeline-info-container">

            <PipelineInfoHeader
                title={props.selectedStep ? props.selectedStep.title : undefined}
                step={props.selectedStepOrder ? props.selectedStepOrder : undefined}
            >
                <PipelineInfoStatus status={props.selectedStep?.status} />
            </PipelineInfoHeader>

            {!props.selectedStep?.sideDetails?.details ? undefined :
                <PipelineInfoDetails data={props.selectedStep.sideDetails.details} />
            }
   
            {!props.selectedStep?.sideDetails?.configuration ? undefined :
                <PipelineInfoConfiguration
                    isSkeleton={!props.selectedInstance}
                    type={props.type}
                    configuration={props.selectedInstance?.configuration}
                />
            }

            {!props.selectedStep?.sideDetails?.webhook ? undefined :
                // Change this to "field" as all other handlings
                <PipelineWebhook link={props.selectedStep.sideDetails.webhook} />
            }

            {!props.selectedStep?.sideDetails?.datalake? undefined :
                <PipelineDataLake 
                    totalFiles={props.selectedStep.sideDetails.datalake.totalFiles}
                    doc={props.selectedStep.sideDetails.datalake.doc}
                    zip={props.selectedStep.sideDetails.datalake.zip}
                />
            }

        </div>
    );
}