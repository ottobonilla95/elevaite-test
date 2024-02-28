"use client";
import { ElevaiteIcons } from "@repo/ui/components";
import { Fragment, useEffect, useState } from "react";
import type { PipelineStep } from "../../../../../lib/interfaces";
import "./PipelineDiagram.scss";
import { PipelineDiagramStep } from "./PipelineDiagramStep";




const DEFAULT_DISPLAY_STEPS: PipelineStep[][] = [
    [{
        id: "default_1",
        title: "Data Source Configuration",
        dependsOn: [],
        data: [],
    }],
    [{
        id: "default_2",
        title: "Worker Progress",
        dependsOn: ["default_1"],
        data: [],
    }],
    [{
        id: "default_3",
        title: "Data Lake Storage",
        dependsOn: ["default_2"],
        data: [],
    }],
];






interface PipelineDiagramProps {
    steps?: PipelineStep[][];
    selectedStepId?: string;
    onSelectedStep?: (step: PipelineStep) => void;
}

export function PipelineDiagram(props: PipelineDiagramProps): JSX.Element {
    const [displaySteps, setDisplaySteps] = useState<PipelineStep[][]>(DEFAULT_DISPLAY_STEPS);



    useEffect(() => {
        setDisplaySteps(DEFAULT_DISPLAY_STEPS);
        // if (props.steps) setDisplaySteps(props.steps);
        // else setDisplaySteps(DEFAULT_DISPLAY_STEPS);
    }, [props.steps]);




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