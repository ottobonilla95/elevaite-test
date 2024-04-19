"use client";
import { ElevaiteIcons, type CommonMenuItem, CommonDialog, CommonInput, CommonSelect, CommonFormLabels } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { specialHandlingModelFields, useModels } from "../../../../lib/contexts/ModelsContext";
import { ModelsStatus, type ModelObject } from "../../../../lib/interfaces";
import { CondensedListRow } from "./CondensedListRow";
import type { RowStructure } from "./ModelsListRow";
import { ModelsListRow } from "./ModelsListRow";
import "./ModelsListTable.scss";


const embeddingTasksArray = [
    "sentence-similarity",
];


enum MENU_ACTIONS {
    DEPLOY = "Deploy",
    DELETE = "Delete",
    EVALUATE = "Evaluate",
};


interface ModelsListTableProps {
    isVisible?: boolean;
    isEmbedding?: boolean;
}

export function ModelsListTable(props: ModelsListTableProps): JSX.Element {
    const modelsContext = useModels();
    const [displayModels, setDisplayModels] = useState<ModelObject[]>([]);
    const [datasetId, setDatasetId] = useState("");
    const [pendingAction, setPendingAction] = useState< undefined | 
        { title: string, action: MENU_ACTIONS, model: ModelObject, label?: string; icon?: React.ReactNode } >();


    const modelsListStructure: RowStructure[] = [
        { header: "Status", field: "status", isSortable: true, specialHandling: specialHandlingModelFields.STATUS },
        { header: "Model Name", field: "name", isSortable: true, onClick: handleModelClick },
        { header: "Model Repo", field: "huggingface_repo", isSortable: true },
        { header: "Model Task", field: "task", isSortable: true },
        { header: "RAM to run", field: "memory_requirements|run", isSortable: true, align: "center", style: "block", specialHandling: specialHandlingModelFields.RAM_TO_RUN },
        { header: "RAM to train", field: "memory_requirements|train", isSortable: true, align: "center", style: "block", specialHandling: specialHandlingModelFields.RAM_TO_TRAIN },
        { header: "Tags", field: "tags", isSortable: true, specialHandling: specialHandlingModelFields.TAGS },
        { header: "Created at", field: "created", isSortable: true, specialHandling: specialHandlingModelFields.DATE, align: "right" },
    ];
    
    
    const modelsListMenu: CommonMenuItem<ModelObject>[] = [
        { label: "Deploy Model", onClick: (item: ModelObject) => { handleMenuClick(item, MENU_ACTIONS.DEPLOY); } },
        { label: "Remove Model", onClick: (item: ModelObject) => { handleMenuClick(item, MENU_ACTIONS.DELETE); } },
        { label: "Evaluate Model", onClick: (item: ModelObject) => { handleMenuClick(item, MENU_ACTIONS.EVALUATE); } },
    ]
    


    useEffect(() => {
        setDisplayModels(modelsContext.models.filter(model => 
            !model.task ? !props.isEmbedding :
            props.isEmbedding ? embeddingTasksArray.includes(model.task) :
            !embeddingTasksArray.includes(model.task)
        ));
    }, [modelsContext.models]);




    function getModelsListMenu(status?: ModelsStatus): CommonMenuItem<ModelObject>[] {
        if (!status || status === ModelsStatus.REGISTERING) return [];
        else if (status === ModelsStatus.DEPLOYED) return [
            { label: "Remove Model", onClick: (item: ModelObject) => { handleMenuClick(item, MENU_ACTIONS.DELETE); } },
            { label: "Evaluate Model", onClick: (item: ModelObject) => { handleMenuClick(item, MENU_ACTIONS.EVALUATE); } },
        ];
        else if (status === ModelsStatus.FAILED) return [
            { label: "Remove Model", onClick: (item: ModelObject) => { handleMenuClick(item, MENU_ACTIONS.DELETE); } },
        ]
        return modelsListMenu;
    }




    
    function handleMenuClick(model: ModelObject, action: MENU_ACTIONS): void {
        switch (action) {
            case MENU_ACTIONS.DEPLOY: setPendingAction({title: "Deploy Model?", action, model}); break;
            case MENU_ACTIONS.EVALUATE: setPendingAction({title: "Evaluate Model", action, model, label: "Evaluate", icon: <ElevaiteIcons.SVGEvaluate/>}); break;
            case MENU_ACTIONS.DELETE: setPendingAction({title: "Delete Model?", action, model}); break;
            default: break;
        }
    }
    
    function handleModelClick(item: ModelObject): void {
        modelsContext.setSelectedModel(item);
    }

    function handleDialogClose(): void {
        setPendingAction(undefined);
    }

    function handleDialogConfirm(): void {
        if (!pendingAction) return;
        switch (pendingAction.action) {
            case MENU_ACTIONS.DEPLOY: void modelsContext.deployModel(pendingAction.model.id); break;
            case MENU_ACTIONS.EVALUATE: void modelsContext.evaluateModel(pendingAction.model.id, datasetId); break;
            case MENU_ACTIONS.DELETE: void modelsContext.deleteModel(pendingAction.model.id.toString()); break;
            default: break;
        }
        handleDialogClose();
    }



    return (
        <div className={[
            "models-list-table-container",
            props.isVisible ? "is-visible" : undefined,
        ].filter(Boolean).join(" ")}>
            {modelsContext.loading.models ? 
                <div className="table-span">
                    <ElevaiteIcons.SVGSpinner/>
                    <span>Loading...</span>
                </div>
            :
            
            modelsContext.selectedModel ? 
                <div className="condensed-grid">
                    
                    {displayModels.length === 0 ? 
                        <div className="table-span empty">
                            There are no models to display.
                        </div>

                    :
                    displayModels.map((model, index) => 
                        <CondensedListRow
                            key={model.id}
                            model={model}
                            structure={modelsListStructure}
                            menu={getModelsListMenu(model.status)}
                            menuToTop={displayModels.length > 4 && index > (displayModels.length - 4) }
                        />
                    )}
                </div>
            :
                <div className="models-list-table-grid">
                    <ModelsListRow isHeader structure={modelsListStructure} menu={getModelsListMenu()} />
                    {displayModels.length === 0 ? 
                        <div className="table-span empty">
                            There are no models to display.
                        </div>

                    :

                    displayModels.map((model, index) => 
                        <ModelsListRow
                            key={model.id}
                            model={model}
                            structure={modelsListStructure}
                            menu={getModelsListMenu(model.status)}
                            menuToTop={displayModels.length > 4 && index > (displayModels.length - 4) }
                        />
                    )}
                </div>
            }


            {!pendingAction ? undefined :
                <CommonDialog
                    title={pendingAction.title}
                    icon={pendingAction.icon}
                    onConfirm={handleDialogConfirm}
                    onCancel={handleDialogClose}
                    confirmLabel={pendingAction.label}
                    dangerSubmit={pendingAction.action === MENU_ACTIONS.DELETE}
                    disableConfirm={pendingAction.action === MENU_ACTIONS.EVALUATE && !datasetId}
                    confirmTooltip={pendingAction.action === MENU_ACTIONS.EVALUATE && !datasetId ? "Please select a dataset" : ""}
                >
                    {pendingAction.action !== MENU_ACTIONS.EVALUATE ? undefined :
                        <div className="evaluation-dialog-container">
                            <CommonInput
                                label="Selected Model"
                                initialValue={pendingAction.model.name}
                                disabled
                            />
                            <CommonFormLabels
                                label="Evaluation Dataset"
                            >
                                <CommonSelect
                                    className="evaluate-dialog-dataset"
                                    options={modelsContext.modelDatasets.map(item => { return {value: item.id.toString(), label: item.name}; })}
                                    onSelectedValueChange={setDatasetId}
                                />
                            </CommonFormLabels>
                        </div>
                    }
                </CommonDialog>
            }


        </div>
    );
}