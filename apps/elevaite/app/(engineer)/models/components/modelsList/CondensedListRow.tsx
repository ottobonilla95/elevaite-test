import { CommonButton, CommonMenu } from "@repo/ui/components";
import dayjs from "dayjs";
import "./CondensedListRow.scss";
import { useModels } from "../../../../lib/contexts/ModelsContext";
import { StatusCell, type ModelListNormalRow } from "./ModelsListRow";




export function CondensedListRow(props: ModelListNormalRow): JSX.Element {
    const modelsContext = useModels();


    function handleNameClick(): void {
        const nameStructure = props.structure.find(item => item.field === "name");
        if (nameStructure?.onClick) {
            nameStructure.onClick(props.model);
        }
    }


    return (
        <div
            className={[
                "condensed-list-row-container",
                modelsContext.selectedModel?.id === props.model.id ? "selected" : undefined,
            ].filter(Boolean).join(" ")}
        >

            <div className="condensed-line">

                {!props.menu ? undefined : 
                    <div className="models-list-row-cell menu">
                        <CommonMenu
                            item={props.model}
                            menu={props.menu}
                        />
                    </div>
                }

                <CommonButton
                    className="models-list-row-cell name"
                    onClick={handleNameClick}
                    overrideClass
                >
                    {props.model.name}
                </CommonButton>

                <span>|</span>

                <div className="models-list-row-cell huggingface_repo">
                    {props.model.huggingface_repo}
                </div>

            </div>


            <div className="condensed-line dark">

                <div className="models-list-row-cell task">
                    {props.model.task}
                </div>

                <span>•</span>

                <div className="models-list-row-cell created_at">
                    {props.model.created_at ? dayjs(props.model.created_at).format("DD-MMM-YYYY hh:mm a") : "Unknown date"}
                </div>

                <div className="condensed-across">
                    {!props.model.status ? undefined : 
                        <StatusCell status={props.model.status} url={props.model.endpointUrl} />
                    }
                </div>
            </div>

        </div>
    );
}