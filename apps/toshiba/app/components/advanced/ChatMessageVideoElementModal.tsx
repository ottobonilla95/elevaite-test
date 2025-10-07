import { CommonButton, CommonModal, ElevaiteIcons, Logos } from "@repo/ui";
import "./ChatMessageVideoElementModal.scss";
import { normalizeYouTubeUrl } from "./ChatMessageVideoElement";



interface ChatMessageVideoElementModalProps {
    isOpen: boolean;
    onClose: () => void;
    videoSrc?: string;
    description?: string;
    videoStartPoint?: number;
    videoEndPoint?: number;
    videoDuration?: number;
    isYouTube?: boolean;
}

export function ChatMessageVideoElementModal(props: ChatMessageVideoElementModalProps): React.ReactNode {
    if (!props.isOpen) return undefined;

    return (
        <CommonModal onClose={props.onClose}>
            <div className="chat-message-video-element-modal-container">

                <div className="controls-container">
                    <CommonButton onClick={props.onClose} noBackground>
                        <ElevaiteIcons.SVGXmark/>
                    </CommonButton>
                </div>

                <div className="modal-video-background">
                    
                    <div className="modal-video-container">

                        {props.videoSrc && props.isYouTube ? 
                            <iframe
                                className="chat-message-video-element-player"
                                src={normalizeYouTubeUrl(props.videoSrc, { start: props.videoStartPoint, end: props.videoEndPoint, autoplay: true })}
                                title="YouTube video"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />
                        :
                            <video
                                className="chat-message-video-element-player"
                                src={props.videoSrc}
                                preload="auto"
                                controls
                                autoPlay
                                onLoadedMetadata={(event) => {
                                    const video = event.currentTarget;
                                    if (props.videoStartPoint && props.videoStartPoint > 0) video.currentTime = props.videoStartPoint;
                                }}
                            >
                                Your browser doesn't support embedded videos.
                            </video>                        
                        }

                    </div>

                </div>

                <div className="modal-video-details-container">
                    <div className="description">{props.description}</div>
                    {!props.videoSrc || !props.isYouTube ? undefined :
                        <a
                            href={normalizeYouTubeUrl(props.videoSrc, { start: props.videoStartPoint ?? 0, directLink: true })}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="youtube-link"
                        >
                            <Logos.Youtube/>
                            <span>Open on Youtube</span>
                        </a>
                    }
                </div>

            </div>
        </CommonModal>
    );
}