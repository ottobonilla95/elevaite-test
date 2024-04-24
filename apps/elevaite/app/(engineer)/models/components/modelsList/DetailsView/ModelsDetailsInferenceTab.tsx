import { CommonButton, ElevaiteIcons, LoadingBar, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import { useEffect, useRef, useState } from "react";
import "./ModelsDetailsInferenceTab.scss";
import dayjs from "dayjs";
import { inferEndpointEmbedding, inferEndpointSummarization, inferEndpointTextGeneration } from "../../../../../lib/actions/modelActions";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { useAutosizeTextArea } from "../../../../../lib/hooks";





interface InferMessageObject {
    id: number;
    isUser: boolean;
    creationDate: string;
    message: string;
}



export function ModelsDetailsInferenceTab(): JSX.Element {
    const modelsContext = useModels();
    const scrollRef = useRef<HTMLDivElement|null>(null);
    const [text, setText] = useState("");
    const textAreaRef = useRef<HTMLTextAreaElement>(null);
    useAutosizeTextArea(textAreaRef.current, text);
    const [isLoading, setIsLoading] = useState(false);
    const [messages, setMessages] = useState<InferMessageObject[]>([]);


    useEffect(() => {
        scrollToBottom();
    }, [messages.length]);


    function handleTextChange(value: string): void {
        if (isLoading) return;
        setText(value);
    }

    function handleSend(): void {
        if (isLoading) return;
        const workingText = text;
        setText("");
        if (!workingText.trim()) return;
        addMessage(workingText, true);
        void inferMessage(workingText);
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }

    function scrollToBottom(): void {
        if (!scrollRef.current) return;
        scrollRef.current.scrollTo({
            top: scrollRef.current.scrollHeight,
            behavior: "smooth",
        })
    }

    function addMessage(passedMessage: string, isUser?: boolean): void {
        setMessages(current => { return [...current, {
            id: current.length + 1,
            isUser: Boolean(isUser),
            creationDate: dayjs().toISOString(),
            message: passedMessage,
        }]; })
    }


    async function inferMessage(message: string): Promise<void> {
        if (!modelsContext.selectedModel?.endpointId) return;
        try {
            setIsLoading(true);
            // Embedding models
            if (modelsContext.selectedModel.task === "sentence-similarity") {
                const inferredSummary = await inferEndpointEmbedding(modelsContext.selectedModel.endpointId, message);
                addMessage(inferredSummary.results.join("\n"), false);

            // Summary
            } else if (modelsContext.selectedModel.task === "summarization") {
                const inferredSummary = await inferEndpointSummarization(modelsContext.selectedModel.endpointId, message);
                if (inferredSummary.results[0]?.summary_text) {
                    addMessage(inferredSummary.results[0]?.summary_text, false);
                }
            
            // Text generation
            } else {
                const inferredText = await inferEndpointTextGeneration(modelsContext.selectedModel.endpointId, message);
                if (inferredText.results[0]?.generated_text) {
                    addMessage(inferredText.results[0]?.generated_text, false);
                }
            }

        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in inferring endpoint:", error);
        } finally {                
            setIsLoading(false);
        }
    }





    return (
        <div className="models-details-inference-tab-container">
            
            <div className="messages-container">
                <div className="messages-header">
                    <div className="name">Model Testing</div>
                    <div className="model">{modelsContext.selectedModel?.task}</div>
                </div>
                <div className="messages-contents">
                    <div className="messages-scroller" ref={scrollRef}>
                        <div className="messages-list">
                            {messages.map(message =>
                                <InferenceMessage key={message.id} {...message} />
                            )}
                        </div>
                    </div>
                </div>
                {!isLoading ? null : 
                    <div className="message-waiting-loader">
                        <LoadingBar/>
                        <span>Waiting for model response. Please wait...</span>
                    </div>
                }
            </div>

            <div className={["chat-input-container", isLoading ? "loading" : undefined].filter(Boolean).join(" ")}>
                {modelsContext.selectedModel?.task === "summarization" ? 
                
                    <SimpleTextarea
                        passedRef={textAreaRef}
                        wrapperClassName="chat-input-field"
                        value={text}
                        onChange={handleTextChange}
                        onKeyDown={handleKeyDown}
                        placeholder={isLoading ? "Please wait..." : "Enter text and press ENTER"}
                        disabled={isLoading}
                        rightIcon={
                            <CommonButton
                                onClick={handleSend}
                                disabled={isLoading}
                            >
                                {isLoading ?
                                    <ElevaiteIcons.SVGSpinner/> :
                                    <ElevaiteIcons.SVGSend/>
                                }
                            </CommonButton>                    
                        }
                    />

                    :

                    <SimpleInput
                        wrapperClassName="chat-input-field"
                        value={text}
                        onChange={handleTextChange}
                        onKeyDown={handleKeyDown}
                        placeholder={isLoading ? "Please wait..." : "Enter text and press ENTER"}
                        disabled={isLoading}
                        rightIcon={
                            <CommonButton
                                onClick={handleSend}
                                disabled={isLoading}
                            >
                                {isLoading ?
                                    <ElevaiteIcons.SVGSpinner/> :
                                    <ElevaiteIcons.SVGSend/>
                                }
                            </CommonButton>                    
                        }
                    />
                }
                
            </div>

        </div>
    );
}




function InferenceMessage(props: InferMessageObject): JSX.Element {
    return(
        <div className={["inference-message-container", props.isUser ? "user" : undefined].filter(Boolean).join(" ")}>
            <div className="inference-message-header">
                <span className="name">{props.isUser ? "User Query" : "Model Response"}</span>
                <span className="secondary">•</span>
                <span className="secondary">{dayjs(props.creationDate).format("MMMM DD, YYYY, hh:mm A")}</span>
            </div>
            <div className="inference-message-contents">
                {props.message}
            </div>
        </div>
    );
}










