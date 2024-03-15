import { useModels } from "../../../../lib/contexts/ModelsContext";
import { ModelsListRow } from "./ModelsListRow";
import "./ModelsListTable.scss";



interface ModelsListTableProps {
    isVisible?: boolean;
}

export function ModelsListTable(props: ModelsListTableProps): JSX.Element {
    const modelsContext = useModels();


    return (
        <div className={[
            "models-list-table-container",
            props.isVisible ? "is-visible" : undefined,
        ].filter(Boolean).join(" ")}>
            <div className="table-grid">
                <ModelsListRow isHeader />
                {modelsContext.models.map(model => <ModelsListRow key={model.id} model={model} />)}
            </div>
        </div>
    );
}