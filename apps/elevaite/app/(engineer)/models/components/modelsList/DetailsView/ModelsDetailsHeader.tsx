import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./ModelsDetailsHeader.scss";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { StatusCell } from "../ModelsListRow";





export function ModelsDetailsHeader(): JSX.Element {
    const modelsContext = useModels();


    function handleClose(): void {
        modelsContext.setSelectedModel(undefined);
    }

    function handleRefresh(): void {
        modelsContext.refreshSelectedModel();
    }

    function handleAddTag(): void {
        console.log("Adding Tag");
    }


    return (
        <div className="models-details-header-container">

            <div className="models-details-header-main">
                <div className="main-icon-container">
                    <ElevaiteIcons.SVGSettings/>
                </div>

                <div className="models-stack">

                    <div className="models-details-line spread">
                        <span>{modelsContext.selectedModel?.name}</span>

                        <div className="models-details-controls-container">
                            <CommonButton
                                onClick={handleRefresh}
                                disabled={modelsContext.loading.currentModelParameters}
                                noBackground
                                title="Refresh model details"
                            >
                                <div className={["refresh-icon", modelsContext.loading.currentModelParameters ? "loading" : undefined].filter(Boolean).join(" ")}>
                                    <ElevaiteIcons.SVGRefresh/>
                                </div>
                            </CommonButton>
                            
                            <CommonButton
                                onClick={handleClose}
                                noBackground
                                title="Close model details"
                            >
                                <ElevaiteIcons.SVGXmark/>
                            </CommonButton>
                        </div>
                    </div>

                    <div className="models-details-line">
                        {!modelsContext.selectedModel?.status ? undefined : 
                            <div className="status-container">
                                <StatusCell status={modelsContext.selectedModel.status} />
                            </div>
                        }
                        {!modelsContext.selectedModel?.task ? undefined :
                            <div className="task-container">{modelsContext.selectedModel.task.split("-").join(" ")}</div>
                        }
                        <div className="id-container">ID</div>
                        <span>{modelsContext.selectedModel?.id}</span>
                    </div>

                </div>

            </div>

            <div className="models-details-tags">
                <CommonButton
                    className="add-tag"
                    onClick={handleAddTag}
                    disabled={modelsContext.loading.currentModelParameters}
                >
                    + Add Tag
                </CommonButton>
                {!modelsContext.selectedModel?.tags ? undefined :
                    modelsContext.selectedModel.tags.map(tag => 
                        <div key={tag} className="tag">{tag}</div>
                    )
                }                
            </div>

        </div>
    );
}