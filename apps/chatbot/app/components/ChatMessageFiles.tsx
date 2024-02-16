import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import { ChatMessageFileObject } from "../lib/interfaces";
import "./ChatMessageFiles.scss";




interface ChatMessageFilesProps {
    files?: ChatMessageFileObject[];
}


export function ChatMessageFiles(props: ChatMessageFilesProps): JSX.Element {


    return (
        <div className="chat-message-files-container">
            {!props.files || props.files.length === 0 ? 
                <div className="no-files">No relevant files</div>
                :
                props.files.map(file => <ChatMessageFile key={file.id} {...file}/>)
            }
        </div>
    );
}



function ChatMessageFile(props: ChatMessageFileObject): JSX.Element {

    return (
        <div className="chat-message-file-container">
            <ChatbotIcons.SVGDocument/>
            <span title={props.filename}>{props.filename}</span>
            <CommonButton disabled={!props.isViewable} title={props.isViewable ? "View file in a new tab" : "This file is not viewable on your browser"}>
                <ChatbotIcons.SVGOpen/>
            </CommonButton>
            <CommonButton disabled={!props.isDownloadable} title={props.isDownloadable ? "Download file" : "This file is not available for download"}>
                <ChatbotIcons.SVGDownload/>
            </CommonButton>
        </div>
    );
}