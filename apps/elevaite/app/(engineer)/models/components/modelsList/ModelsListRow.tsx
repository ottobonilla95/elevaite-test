import dayjs from "dayjs";
import { ModelObject, ModelsStatus } from "../../../../lib/interfaces";
import "./ModelsListRow.scss";
import { ElevaiteIcons } from "@repo/ui/components";




interface ModelListNormalRow {
    model: ModelObject;
}

interface ModelListHeaderRow {
    isHeader: true;
    model?: never;
}

type ModelsListRowProps = ModelListNormalRow | ModelListHeaderRow;

export function ModelsListRow(props: ModelsListRowProps): JSX.Element {






    return (
        <div className={["models-list-row-container", "isHeader" in props ? "header" : undefined].filter(Boolean).join(" ")}>
            <div className="name">{"isHeader" in props ? "Model Name" : props.model.name }</div>
            <div className="id">{"isHeader" in props ? "Model ID" : props.model.id }</div>
            <div className="type">{"isHeader" in props ? "Model Type" : props.model.model_type }</div>
            <div className="status">{"isHeader" in props ? "Status" : <StatusCell status={props.model.status}/> }</div>
            <div className="tags">{"isHeader" in props ? "Tags" : props.model.tags.map(tag => 
                <div className="tag" key={tag}>{tag}</div>
                ) }</div>
            <div className="node cpu">{"isHeader" in props ? "CPU" : props.model.node.cpu }</div>
            <div className="node gpu">{"isHeader" in props ? "GPU" : props.model.node.gpu }</div>
            <div className="node ram">{"isHeader" in props ? "RAM" : props.model.node.ram }</div>
            <div className="created">{"isHeader" in props ? "Created at" : dayjs(props.model.date_created).format("DD-MMM-YYYY hh:mm a") }</div>
        </div>
    );
}



function StatusCell({status}: {status: ModelsStatus}): JSX.Element {
    return (
        <div className={["status-cell", status].join(" ")}>
            {status === ModelsStatus.ACTIVE ? <ElevaiteIcons.SVGCheckmark/> : 
            status === ModelsStatus.REGISTERING ? <ElevaiteIcons.SVGInstanceProgress/> :
            <ElevaiteIcons.SVGXmark/>
            }
            {status === ModelsStatus.ACTIVE ? "Active" : 
            status === ModelsStatus.REGISTERING ? "Registering" :
            "Failed"
            }
        </div>
    );
}