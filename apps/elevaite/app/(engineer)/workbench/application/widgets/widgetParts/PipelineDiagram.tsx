"use client";
import { ElevaiteIcons } from "@repo/ui/components";
import { Fragment, useEffect, useState } from "react";
import { S3DataRetrievalAppPipelineStructure } from "../../../../../lib/dataRetrievalApps";
import type { PipelineStep } from "../../../../../lib/interfaces";
import { ApplicationType } from "../../../../../lib/interfaces";
import { S3PreprocessingAppPipelineStructure } from "../../../../../lib/preprocessingApps";
import "./PipelineDiagram.scss";
import { PipelineDiagramStep } from "./PipelineDiagramStep";




const DEFAULT_DISPLAY_STEPS: PipelineStep[][] = [
    [{
        id: "default_1",
        title: "Data Source Configuration",
        previousStepIds: [],
        nextStepIds: [],
        data: [],
    }],
];






interface PipelineDiagramProps {    
    type?: ApplicationType;
    steps?: PipelineStep[][];
    selectedStepId?: string;
    onSelectedStep?: (step: PipelineStep, stepOrder?: string) => void;
}

export function PipelineDiagram(props: PipelineDiagramProps): JSX.Element {
    const [displaySteps, setDisplaySteps] = useState<PipelineStep[][]>(DEFAULT_DISPLAY_STEPS);


    useEffect(() => {
        if (props.steps && props.steps.length > 0) setDisplaySteps(props.steps);
        else if (props.type) setDisplaySteps(props.type === ApplicationType.INGEST ? S3DataRetrievalAppPipelineStructure : S3PreprocessingAppPipelineStructure);
        else setDisplaySteps(DEFAULT_DISPLAY_STEPS);
    }, [props.steps, props.type]);




    return (
        <div className="pipeline-diagram-container">
            <div className="diagram-content">
                {/* <div className="flow-start">
                    <div className="backdrop" />
                    <span>Start</span>
                </div> */}

                {displaySteps.map((stepGroup, index) => 
                
                    // eslint-disable-next-line react/no-array-index-key -- This array is made specifically to group things into an order.
                    <Fragment key={index}>
                        {index === 0 ? null : 
                            <div className="diagram-arrow-container">
                                {stepGroup.map(step => <ElevaiteIcons.SVGArrowLong key={step.id} type="down" />)}
                            </div>
                        }
                        <div className="diagram-group-container">
                            {stepGroup.map(step => 
                                <PipelineDiagramStep
                                    key={step.id}
                                    stepNumber={index}
                                    endStep={displaySteps.length-1}
                                    selectedStepId={props.selectedStepId}
                                    onSelectedStep={props.onSelectedStep}
                                    {...step}
                                />
                            )}
                        </div>
                    </Fragment>
                )}

            </div>
        </div>
    );
}