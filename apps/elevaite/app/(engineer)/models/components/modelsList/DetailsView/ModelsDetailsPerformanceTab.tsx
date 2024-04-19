import { ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { EvaluationStatus, type EvaluationObject } from "../../../../../lib/interfaces";
import "./ModelsDetailsPerformanceTab.scss";


interface ModelsDetailsPerformanceProps {
    evaluations: EvaluationObject[];
    onEvaluationsChange: (evaluations: EvaluationObject[]) => void;
}


export function ModelsDetailsPerformanceTab(props: ModelsDetailsPerformanceProps): JSX.Element {
    const modelsContext = useModels();

    useEffect(() => {
        if (!modelsContext.selectedModel) return;
        void getModelEvaluations(modelsContext.selectedModel.id);
    }, [modelsContext.selectedModel]);
   

    async function getModelEvaluations(modelId: string|number): Promise<void> {
        const evaluations = await modelsContext.getModelEvaluations(modelId);
        props.onEvaluationsChange(evaluations);
    }


    return (
        <div className="models-details-performance-tab-container">
            {props.evaluations.length === 0 ? 
                <div className="no-evaluations">There are no evaluations for this model.</div>
                :
                props.evaluations.map(evaluation => 
                    <ModelDetailsEvaluationBlock
                        key={evaluation.id}
                        {...evaluation}
                    />
                )
            }
        </div>
    );
}





function ModelDetailsEvaluationBlock(props: EvaluationObject): JSX.Element {
    const models = useModels();
    const [datasetName, setDatasetName] = useState("");
    const [icon, setIcon] = useState<React.ReactNode>();

    useEffect(() => {
        if (!props.dataset_id) { setDatasetName(""); return; }
        const dataset = models.modelDatasets.find(item => item.id === props.dataset_id);
        if (dataset) setDatasetName(dataset.name);
    }, [props.dataset_id]);

    useEffect(() => {
        switch (props.status) {
            case EvaluationStatus.EVALUATING: setIcon(<ElevaiteIcons.SVGInstanceProgress className="orange" />); break;
            case EvaluationStatus.FAILED: setIcon(<ElevaiteIcons.SVGXmark className="red" />); break;
            case EvaluationStatus.SUCCESS: setIcon(<ElevaiteIcons.SVGCheckmark className="green" />); break;
            default: setIcon(<ElevaiteIcons.SVGSpinner/>); break;
        }
    }, [props.status]);

    return (
        <div className="model-evaluation-block-container">

            <div className="evaluation-header">
                <div className="icon">
                    {icon}
                </div>
                <div className="evaluation-header-contents">
                    <div className="header-row top">
                        <div>
                            {`${dayjs().format("MMMM DD, YYYY")} Evaluation`}
                        </div>
                        <span>•</span>
                        <span>{datasetName}</span>
                        <div className="user-container">
                            Unknown User
                        </div>
                    </div>
                    <div className="header-row bottom">
                        {dayjs().format("hh:mm A")}
                    </div>
                </div>
            </div>

            <div className="evaluation-contents">
                {props.status === EvaluationStatus.FAILED ? 
                    <div className="evaluation-message">
                        <span>This evaluation has failed.</span>
                    </div>
                : props.status === EvaluationStatus.EVALUATING ?                     
                    <div className="evaluation-message">
                        <span>Evaluating...</span>
                    </div>
                :
                    <>
                        <div className="label">Latency:</div>
                        <div className="value">Test</div>
                        <div className="label">Processor:</div>
                        <div className="value">Test</div>
                        <div className="label">Cost per Token:</div>
                        <div className="value">Test</div>
                    </>
                }
            </div>

        </div>
    )
}
