import type { CommonMenuItem } from "@repo/ui/components";
import { specialHandlingModelFields, useModels } from "../../../../lib/contexts/ModelsContext";
import type { ModelObject } from "../../../../lib/interfaces";
import type { RowStructure } from "./ModelsListRow";
import { ModelsListRow } from "./ModelsListRow";
import "./ModelsListTable.scss";
import { CondensedListRow } from "./CondensedListRow";




interface ModelsListTableProps {
    isVisible?: boolean;
}

export function ModelsListTable(props: ModelsListTableProps): JSX.Element {
    const modelsContext = useModels();


    const modelsListStructure: RowStructure[] = [
        { header: "Status", field: "status", isSortable: true, specialHandling: specialHandlingModelFields.STATUS },
        { header: "Model Name", field: "name", isSortable: true, onClick: handleModelClick },
        { header: "Model Repo", field: "huggingface_repo", isSortable: true },
        { header: "Model Task", field: "task", isSortable: true },
        { header: "RAM to run", field: "ramToRun", isSortable: true, align: "center", style: "block" },
        { header: "RAM to train", field: "ramToTrain", isSortable: true, align: "center", style: "block" },
        { header: "Tags", field: "tags", isSortable: true, specialHandling: specialHandlingModelFields.TAGS },
        { header: "Created at", field: "date_created", isSortable: true, specialHandling: specialHandlingModelFields.DATE, align: "right" },
    ];
    
    
    const modelsListMenu: CommonMenuItem<ModelObject>[] = [
        { label: "Deploy Model", onClick: (item: ModelObject) => { handleMenuClick(item, "deploy"); } },
        { label: "Archive Model", onClick: (item: ModelObject) => { handleMenuClick(item, "archive"); } },
        { label: "Evaluate Model", onClick: (item: ModelObject) => { handleMenuClick(item, "evaluate"); } },
        { label: "Launch Model QA", onClick: (item: ModelObject) => { handleMenuClick(item, "qa"); } },
    ]
    
    
    function handleMenuClick(item: ModelObject, action: string): void {
        console.log("item", item, "action:", action);
    }
    
    function handleModelClick(item: ModelObject): void {
        modelsContext.setSelectedModel(item);
    }



    return (
        <div className={[
            "models-list-table-container",
            props.isVisible ? "is-visible" : undefined,
        ].filter(Boolean).join(" ")}>
            {modelsContext.selectedModel ? 
                <div className="condensed-grid">
                    {modelsContext.models.map(model => 
                        <CondensedListRow key={model.id} model={model} structure={modelsListStructure} menu={modelsListMenu} />
                    )}
                </div>
            :
                <div className="models-list-table-grid">
                    <ModelsListRow isHeader structure={modelsListStructure} menu={modelsListMenu} />
                    {modelsContext.models.map(model => 
                        <ModelsListRow key={model.id} model={model} structure={modelsListStructure} menu={modelsListMenu} />
                    )}
                </div>
            }
        </div>
    );
}