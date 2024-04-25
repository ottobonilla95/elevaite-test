import { CommonButton, ElevaiteIcons, LoadingBar, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useRef, useState } from "react";
import { inferEndpointEmbedding, inferEndpointQuestionAnswering, inferEndpointSummarization, inferEndpointTextGeneration } from "../../../../../lib/actions/modelActions";
import { useModels } from "../../../../../lib/contexts/ModelsContext";
import { getPearsonCorrelation } from "../../../../../lib/helpers";
import { useAutosizeTextArea } from "../../../../../lib/hooks";
import "./ModelsDetailsInferenceTab.scss";



enum SpecialHandlingTasks {
    SentenceSimilarity = "sentence-similarity",
    Summarization = "summarization",
    QuestionAnswering = "question-answering",
};

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
    const [secondaryText, setSecondaryText] = useState("");
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

    function handleSecondaryTextChange(value: string): void {
        if (isLoading) return;
        setSecondaryText(value);
    }

    function handleSend(): void {
        if (isLoading) return;
        const workingText = text;
        const workingSecondaryText = secondaryText;
        setText("");
        setSecondaryText("");
        if (!workingText.trim()) return;
        addMessage(workingText, true, workingSecondaryText);
        void inferMessage(workingText, workingSecondaryText);
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

    function addMessage(passedMessage: string, isUser?: boolean, secondaryMessage?: string): void {
        setMessages(current => { return [...current, {
            id: current.length + 1,
            isUser: Boolean(isUser),
            creationDate: dayjs().toISOString(),
            message: 
                secondaryMessage ? 
                modelsContext.selectedModel?.task === SpecialHandlingTasks.SentenceSimilarity ? 
                    `Source sentence: ${secondaryMessage}\nTesting sentence: ${passedMessage}`
                : modelsContext.selectedModel?.task === SpecialHandlingTasks.QuestionAnswering ? 
                    `Context: ${secondaryMessage}\nQuestion: ${passedMessage}`
                : ""
                : passedMessage,
        }]; })
    }


    async function inferMessage(message: string, secondaryMessage?: string): Promise<void> {
        if (!modelsContext.selectedModel?.endpointId) return;
        try {
            setIsLoading(true);
            // Embedding models
            if (modelsContext.selectedModel.task === SpecialHandlingTasks.SentenceSimilarity) {
                const inferredSimilarity = await inferEndpointEmbedding(modelsContext.selectedModel.endpointId, message, secondaryMessage);
                let similarityIndex: number|undefined;
                if (inferredSimilarity.results.length === 2) {
                    similarityIndex = getPearsonCorrelation(inferredSimilarity.results[0], inferredSimilarity.results[1]);
                }
                const result = similarityIndex !== undefined ? 
                        `The similarity index of the sentences is ${similarityIndex.toString()}`
                    : `The evaluation of sentence similarity has failed.`;
                addMessage(result, false);

            // Summary
            } else if (modelsContext.selectedModel.task === SpecialHandlingTasks.Summarization) {
                const inferredSummary = await inferEndpointSummarization(modelsContext.selectedModel.endpointId, message);
                if (inferredSummary.results[0]?.summary_text) {
                    addMessage(inferredSummary.results[0]?.summary_text, false);
                }
                
            // Question answering
            } else if (modelsContext.selectedModel.task === SpecialHandlingTasks.QuestionAnswering) {
                const inferredQA = await inferEndpointQuestionAnswering(modelsContext.selectedModel.endpointId, message, secondaryMessage);
                addMessage(inferredQA.results.answer);
            
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
                {modelsContext.selectedModel?.task === SpecialHandlingTasks.Summarization ? 
                
                    <SimpleTextarea
                        passedRef={textAreaRef}
                        wrapperClassName="chat-input-field"
                        value={text}
                        onChange={handleTextChange}
                        onKeyDown={handleKeyDown}
                        placeholder={isLoading ? "Please wait..." : "Enter text to be summarized"}
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
                    <>
                        {modelsContext.selectedModel?.task !== SpecialHandlingTasks.SentenceSimilarity 
                            && modelsContext.selectedModel?.task !== SpecialHandlingTasks.QuestionAnswering ? undefined :
                            <SimpleInput
                                wrapperClassName="chat-input-field"
                                value={secondaryText}
                                onChange={handleSecondaryTextChange}
                                placeholder={isLoading ? "Please wait..." : 
                                    modelsContext.selectedModel.task === SpecialHandlingTasks.SentenceSimilarity ? "Enter source sentence"
                                    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- we may apply more conditionals here
                                    : modelsContext.selectedModel.task === SpecialHandlingTasks.QuestionAnswering ? "Enter context"
                                    : "Enter secondary text"
                                }
                                disabled={isLoading}
                            />
                        }
                        <SimpleInput
                            wrapperClassName="chat-input-field"
                            value={text}
                            onChange={handleTextChange}
                            onKeyDown={handleKeyDown}
                            placeholder={isLoading ? "Please wait..." : 
                            modelsContext.selectedModel?.task === SpecialHandlingTasks.SentenceSimilarity ? "Enter testing sentence"
                                : modelsContext.selectedModel?.task === SpecialHandlingTasks.QuestionAnswering ? "Enter question"
                                : "Enter text"}
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
                    </>
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










