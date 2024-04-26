import { CommonButton, CommonModal } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type AppInstanceObject } from "../../../../../lib/interfaces";
import "./PipelineChunks.scss";
import { isObject } from "../../../../../lib/actions/generalDiscriminators";




interface PipelineChunksProps {
    selectedInstance?: AppInstanceObject;
}

export function PipelineChunks(props: PipelineChunksProps): JSX.Element {
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [collectionId, setCollectionId] = useState("");
    
    useEffect(() => {
        setCollectionId(getCollectionIdFromInstance(props.selectedInstance));
    }, [props.selectedInstance]);

    
    function getCollectionIdFromInstance(selectedInstance?: AppInstanceObject): string {
        if (!selectedInstance?.configurationRaw) return "";
        const parsedConfiguration = JSON.parse(selectedInstance.configurationRaw) as unknown;
        if (isObject(parsedConfiguration) && "collectionId" in parsedConfiguration && typeof parsedConfiguration.collectionId === "string") {
            return parsedConfiguration.collectionId;
        }
        return "";
    }

    function handleOpenModal(): void {
        setIsModalVisible(true);
    }

    function handleCloseModal(): void {
        setIsModalVisible(false);
    }


    return (
        <div className="pipeline-chunks-container">
            <CommonButton
                className="chunks-button"
                onClick={handleOpenModal}
            >
                Show Collection Chunks
            </CommonButton>

            {!isModalVisible ? undefined :
                <CommonModal
                    onClose={handleCloseModal}
                >
                    Testing modal
                </CommonModal>
            }


        </div>
    );
}