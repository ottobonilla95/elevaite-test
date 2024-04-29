import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { getCollectionScroll } from "../../../../../lib/actions/applicationActions";
import { isObject } from "../../../../../lib/actions/generalDiscriminators";
import { useRoles } from "../../../../../lib/contexts/RolesContext";
import { type AppInstanceObject, type CollectionChunkObject } from "../../../../../lib/interfaces";
import "./PipelineChunks.scss";




interface PipelineChunksProps {
    selectedInstance?: AppInstanceObject;
}

export function PipelineChunks(props: PipelineChunksProps): JSX.Element {
    const rbac = useRoles();
    const [firstLoading, setFirstLoading] = useState(true);
    const [loading, setLoading] = useState(false);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [collectionId, setCollectionId] = useState("");
    const [collectionChunks, setCollectionChunks] = useState<CollectionChunkObject[]>([]);
    const [nextChunkId, setNextChunkId] = useState<string|null|undefined>();
    

    useEffect(() => {
        setCollectionId(getCollectionIdFromInstance(props.selectedInstance));
        setCollectionChunks([]);
        setNextChunkId(undefined);
    }, [props.selectedInstance]);

    useEffect(() => {
        if (collectionId && rbac.selectedProject?.id) {
            void getCollectionOfInstance(rbac.selectedProject.id, collectionId);
        }
    }, [collectionId]);



    async function getCollectionOfInstance(passedProjectId: string, passedCollectionId: string, nextEntryId?: string): Promise<void> {
        try {
            setLoading(true);
            const fetchedScrollPage = await getCollectionScroll(passedProjectId, passedCollectionId, nextEntryId);
            if (fetchedScrollPage.length === 0) {
                setCollectionChunks([]);
                setNextChunkId(null);
            } else {
                setNextChunkId(fetchedScrollPage[1]);
                setCollectionChunks(current => [...current, ...fetchedScrollPage[0]]);
            }
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching collection page:", error);
        } finally {
            setFirstLoading(false);
            setLoading(false);
        }
    }

    
    function getCollectionIdFromInstance(selectedInstance?: AppInstanceObject): string {
        if (!selectedInstance?.configurationRaw) return "";
        const parsedConfiguration = JSON.parse(selectedInstance.configurationRaw) as unknown;
        if (isObject(parsedConfiguration) && "collectionId" in parsedConfiguration && typeof parsedConfiguration.collectionId === "string") {
            return parsedConfiguration.collectionId;
        }
        return "";
    }

    function handleLoadMore(): void {
        if (nextChunkId && collectionId && rbac.selectedProject?.id) {
            void getCollectionOfInstance(rbac.selectedProject.id, collectionId, nextChunkId);
        }
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
                disabled={!props.selectedInstance}
            >
                Show Collection Chunks
            </CommonButton>

            {!isModalVisible ? undefined :
                <CommonModal
                    onClose={handleCloseModal}
                >
                    <div className="pipeline-chunks-modal-contents">
                        <div className="chunks-header">
                            <div className="chunks-title">
                                {/* <div className="title-icon">
                                    <ElevaiteIcons.SVGRegister/>
                                </div> */}
                                <span>Collection Chunks</span>
                            </div>
                            <div className="close-button">                    
                                <CommonButton onClick={handleCloseModal} noBackground>
                                    <ElevaiteIcons.SVGXmark/>
                                </CommonButton>
                            </div>
                        </div>

                        <div className="chunks-scroller">
                            <div className="chunks-contents">

                                {firstLoading ? 
                                    <div className="first-loading">
                                        <ElevaiteIcons.SVGSpinner/>
                                        <span>Loading...</span>
                                    </div>
                                : collectionChunks.length === 0 ? 
                                    <div className="empty">No chunk information</div>
                                :
                                collectionChunks.map(chunk =>
                                    <ChunkBox key={chunk.id} chunk={chunk} />
                                )}

                                {firstLoading || !nextChunkId ? undefined :
                                    <div className={["load-more", loading ? "loading" : undefined].filter(Boolean).join(" ")}>
                                        <CommonButton
                                            onClick={handleLoadMore}
                                            disabled={loading}
                                            noBackground
                                        >
                                            {loading ? 
                                                <ElevaiteIcons.SVGSpinner/>
                                                :
                                                <span>Load More</span>
                                            }
                                            
                                        </CommonButton>
                                    </div>
                                }

                            </div>
                        </div>

                    </div>
                </CommonModal>
            }


        </div>
    );
}




interface ChunkBoxProps {
    chunk: CollectionChunkObject;
}

function ChunkBox({chunk}: ChunkBoxProps): JSX.Element {
    return (
        <div className="chunk-box-container">
            <div className="token">
                <div className="label">Token Size:</div>
                <div className="value">{chunk.payload?.metadata?.tokenSize?.toString() ?? "None"}</div>
            </div>
            <div className="chunk-id">{chunk.id}</div>
            
            <div className="label">Document Title:</div>
            <div className="value">{chunk.payload?.metadata?.document_title?.trim() ?? "None"}</div>
            
            <div className="label">Page Title:</div>
            <div className="value">{chunk.payload?.metadata?.page_title?.trim() ?? "None"}</div>
            
            <div className="label">Page Content:</div>
            <div className="value">{chunk.payload?.page_content?.trim() ?? "None"}</div>
            
            <div className="label">Source:</div>
            <div className="value">{chunk.payload?.metadata?.source?.trim() ?? "None"}</div>
            
            <div className="label">Vectors:</div>
            <div className="value">{chunk.vector && chunk.vector.length > 0 ? 
                chunk.vector.slice(0, 10).join(", ") : "None"}</div>

            <div className="token">
                <div className="label">Total Vectors:</div>
                <div className="value">{chunk.vector?.length.toString() ?? "None"}</div>
            </div>
                    
        </div>
    );
}

