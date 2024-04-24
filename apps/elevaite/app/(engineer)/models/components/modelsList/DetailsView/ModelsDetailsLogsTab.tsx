"use client";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { type EvaluationObject, type ModelEvaluationLogObject, type ModelRegistrationLogObject } from "../../../../../lib/interfaces";
import { ModelsDetailsLogBlock } from "./ModelsDetailsLogBlock";
import "./ModelsDetailsLogsTab.scss";


const DEFAULT_MODEL_BLOCK = "registration";

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
    const [initialLoading, setInitialLoading] = useState(0);


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

    useEffect(() => {
        if (initialLoading < 2) return;
        if (modelLogs.length > 0 && evaluationLogs.length === 0) setSelectedBlock(DEFAULT_MODEL_BLOCK);
        else if (modelLogs.length === 0 && evaluationLogs.length === 1) setSelectedBlock(evaluationLogs[0].id);
    }, [initialLoading]);


    async function getModelLogs(modelId: string|number): Promise<void> {
        const logs = await modelsContext.getModelLogs(modelId);
        setModelLogs(logs.reverse());
        setInitialLoading(current => current+1);
    }

    async function getEvaluationLogs(evaluationId: string|number): Promise<void> {
        const evalLogs = await modelsContext.getEvaluationLogs(evaluationId);
        setEvaluationLogs(current => [...current, {
            id: evaluationId.toString(),
            logs: evalLogs.reverse(),
            date: dayjs().toISOString(),
        }]);
        setInitialLoading(current => current+1);
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
                    id={DEFAULT_MODEL_BLOCK}
                    logs={modelLogs}
                    isLoading={modelsContext.loading.modelLogs}
                    isHidden={Boolean(selectedBlock) && selectedBlock !== DEFAULT_MODEL_BLOCK}
                    isOpen={selectedBlock === DEFAULT_MODEL_BLOCK}
                    onToggleSize={handleSelect}
                />
            }
            
        </div>
    );
}


