import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import "./ActionsBar.scss";



interface ActionsBarProps {
    onUpvote?: () => void;
    onDownvote?: () => void;
    onRefresh?: () => void;
    onFlag?: () => void;
    onCopy?: () => void;
}

export function ActionsBar(props: ActionsBarProps): JSX.Element {
    return (
        <div className="actions-bar-container">
            {!props.onUpvote && !props.onDownvote ? undefined :
                !props.onDownvote ? <CommonButton className="action-button" onClick={props.onUpvote}>
                                        <ChatbotIcons.SVGActionUpvote/><span>Upvote</span>
                                    </CommonButton> :
                !props.onUpvote ? <CommonButton className="action-button" onClick={props.onDownvote}>
                                    <ChatbotIcons.SVGActionDownvote/><span>Downvote</span>
                                </CommonButton> :
                <div className="combined-button">
                    <CommonButton className="action-button" onClick={props.onUpvote}>
                        <ChatbotIcons.SVGActionUpvote/><span>Upvote</span>
                    </CommonButton>
                    <CommonButton className="action-button" onClick={props.onDownvote}>
                        <ChatbotIcons.SVGActionDownvote/>
                    </CommonButton>
                </div>
            }

            {!props.onRefresh ? undefined :
                <CommonButton className="action-button" onClick={props.onRefresh}>
                    <ChatbotIcons.SVGActionRefresh/><span>Refresh</span>
                </CommonButton>
            }

            {!props.onFlag ? undefined :
                <CommonButton className="action-button" onClick={props.onFlag}>
                    <ChatbotIcons.SVGActionFlag/><span>Flag</span>
                </CommonButton>
            }

            {!props.onCopy ? undefined :
                <CommonButton className="action-button" onClick={props.onCopy}>
                    <ChatbotIcons.SVGActionCopy/><span>Copy</span>
                </CommonButton>
            }
        </div>
    );
}