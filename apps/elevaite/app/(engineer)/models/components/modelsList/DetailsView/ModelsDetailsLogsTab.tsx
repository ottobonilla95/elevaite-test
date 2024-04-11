"use client";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { type EvaluationObject, type ModelEvaluationLogObject, type ModelRegistrationLogObject } from "../../../../../lib/interfaces";
import { ModelsDetailsLogBlock } from "./ModelsDetailsLogBlock";
import "./ModelsDetailsLogsTab.scss";



interface EvaluationLog {
    id: string;
    logs: ModelEvaluationLogObject[],
    date: string;
}



interface ModelsDetailsLogsProps {
    evaluations: EvaluationObject[];
}

export function ModelsDetailsLogsTab(props: ModelsDetailsLogsProps): JSX.Element {
    const modelsContext = useModels();
    const [selectedBlock, setSelectedBlock] = useState("");
    const [modelLogs, setModelLogs] = useState<ModelRegistrationLogObject[]>([]);
    const [evaluationIds, setEvaluationIds] = useState<string[]>([]);
    const [evaluationLogs, setEvaluationLogs] = useState<EvaluationLog[]>([]);


    useEffect(() => {
        if (!modelsContext.selectedModel) return;
        void getModelLogs(modelsContext.selectedModel.id);
    }, [modelsContext.selectedModel]);

    useEffect(() => {
        setEvaluationIds(props.evaluations.map(item => item.id.toString()));
    }, [props.evaluations]);

    useEffect(() => {
        for (const id of evaluationIds) {
            void getEvaluationLogs(id);
        }
    }, [evaluationIds.length]);


    async function getModelLogs(modelId: string|number): Promise<void> {
        const logs = await modelsContext.getModelLogs(modelId);
        setModelLogs(logs.reverse());
    }

    async function getEvaluationLogs(evaluationId: string|number): Promise<void> {
        const evalLogs = await modelsContext.getEvaluationLogs(evaluationId);
        setEvaluationLogs(current => [...current, {
            id: evaluationId.toString(),
            logs: evalLogs.reverse(),
            date: dayjs().toISOString(),
        }]);
    }


    function handleSelect(id: string): void {
        setSelectedBlock(current => current === id ? "" : id);
    }


    return (
        <div className={[
            "models-details-logs-tab-container",
            selectedBlock ? "selected" : undefined,
        ].filter(Boolean).join(" ")}>

            {evaluationLogs.length === 0 ? undefined :
                evaluationLogs.map(item =>
                    <ModelsDetailsLogBlock
                        key={item.id}
                        id={item.id}
                        logs={item.logs}
                        date={item.date}
                        // isLoading={modelsContext.loading.modelLogs}
                        isHidden={Boolean(selectedBlock) && selectedBlock !== item.id}
                        isOpen={selectedBlock === item.id}
                        onToggleSize={handleSelect}
                    />
                )
            }

            {modelLogs.length === 0 ? undefined :
                <ModelsDetailsLogBlock
                    id="registration"
                    logs={modelLogs}
                    isLoading={modelsContext.loading.modelLogs}
                    isHidden={Boolean(selectedBlock) && selectedBlock !== "registration"}
                    isOpen={selectedBlock === "registration"}
                    onToggleSize={handleSelect}
                />
            }
            
        </div>
    );
}


