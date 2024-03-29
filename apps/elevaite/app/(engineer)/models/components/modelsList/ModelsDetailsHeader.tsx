import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./ModelsDetailsHeader.scss";
import { useModels } from "../../../../lib/contexts/ModelsContext";
import { StatusCell } from "./ModelsListRow";



interface ModelsDetailsHeaderProps {

}

export function ModelsDetailsHeader(props: ModelsDetailsHeaderProps): JSX.Element {
    const modelsContext = useModels();


    return (
        <div className="models-details-header-container">

            <div className="models-details-header-main">
                <div className="main-icon-container">
                    <ElevaiteIcons.SVGSettings/>
                </div>

                <div className="models-stack">

                    <div className="models-details-line spread">
                        <span>My Model</span>

                        <div className="models-details-controls-container">
                            <CommonButton
                                noBackground
                            >
                                <ElevaiteIcons.SVGRefresh/>
                            </CommonButton>
                            
                            <CommonButton
                                noBackground
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
                        <div className="id-container">ID</div>
                        <span>{modelsContext.selectedModel?.id}</span>
                    </div>

                </div>

            </div>

            <div className="models-details-tags">
                <div className="add-tag">+ Add Tag</div>
                <div className="tag">Finance</div>
            </div>

        </div>
    );
}