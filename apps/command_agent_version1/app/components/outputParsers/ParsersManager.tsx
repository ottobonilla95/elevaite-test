import { CommonToggle } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { usePrompt } from "../../ui/contexts/PromptContext";
import { type ProcessedPage, type regenerateResponseObject } from "../../lib/interfaces/prompts";
import { DocumentHeadersParser } from "./DocumentHeadersParser";
import { GeneratedPromptParser } from "./GeneratedPromptParser";
import { LineItemsParser } from "./LineItemsParser";
import "./ParsersManager.scss";



interface ParsersManagerProps {
    display: "output" | "prompt";
}

export function ParsersManager({ display }: ParsersManagerProps): JSX.Element {
    const promptContext = usePrompt();
    const [showJSON, setShowJSON] = useState(false);
    const [activeResult, setActiveResult] = useState<regenerateResponseObject | ProcessedPage | null>(null);


    useEffect(() => {
        setActiveResult(promptContext.output ?? promptContext.processedCurrentPage ?? null);
    }, [promptContext.output, promptContext.processedCurrentPage]);


    return (
        <div className="parsers-manager-container">

            {display === "prompt" ?
                <GeneratedPromptParser prompt={activeResult?.prompt} />
                :
                <>
                    <CommonToggle
                        checked={showJSON}
                        onChange={setShowJSON}
                        label="JSON"
                        className="json-toggle"
                    />
                    <DocumentHeadersParser                    
                        result={activeResult?.result}
                        isJSON={showJSON}
                    />
                    <LineItemsParser
                        lineItems={activeResult?.result.line_items}
                        isJSON={showJSON}
                    />
                </>
            }

        </div>
    );
}