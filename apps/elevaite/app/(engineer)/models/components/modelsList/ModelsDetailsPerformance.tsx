import { useEffect, useState } from "react";
import { useModels } from "../../../../lib/contexts/ModelsContext";
import type { EvaluationObject } from "../../../../lib/interfaces";
import "./ModelsDetailsPerformance.scss";



export function ModelsDetailsPerformance(): JSX.Element {
    const modelsContext = useModels();
    const [currentEvaluations, setCurrentEvaluations] = useState<EvaluationObject[]>([]);


    useEffect(() => {
        if (!modelsContext.selectedModel) setCurrentEvaluations([]);
        else {
            setCurrentEvaluations(modelsContext.evaluations.filter(item => item.modelId.toString() === modelsContext.selectedModel?.id.toString()));
        }
    }, [modelsContext.selectedModel, modelsContext.evaluations]);


    return (
        <div className="models-details-performance-container">
            {currentEvaluations.length === 0 ? 
                <div className="no-evaluations">There are no evaluations for this model.</div>
                :
                currentEvaluations.map(evaluation => 
                    <ModelDetailsEvaluationBlock
                        key={`${evaluation.modelId}_${evaluation.name}`}
                        {...evaluation}
                    />
                )
            }
        </div>
    );
}





function ModelDetailsEvaluationBlock(props: EvaluationObject): JSX.Element {
    return (
        <div className="model-evaluation-block-container">

            <div className="evaluation-header">
                <div className="evaluation-name">
                    {props.name}
                </div>
                <span>{props.userName ? props.userName : "Unknown user"}</span>
                <span>•</span>
                <span>{props.date ? props.date : "Unknown date"}</span>
            </div>

            <div className="evaluation-contents">
                <div className="label">Dataset Name:</div>
                <div className="value">{props.dataset}</div>
                <div className="label">Latency:</div>
                <div className="value">{props.latency}</div>
                <div className="label">Processor:</div>
                <div className="value">{props.processor}</div>
                <div className="label">Cost per Token:</div>
                <div className="value">{props.costPerToken}</div>
            </div>

        </div>
    )
}
