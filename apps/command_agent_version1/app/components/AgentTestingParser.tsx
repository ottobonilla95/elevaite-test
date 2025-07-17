import { useEffect, useState } from "react";
import "./AgentTestingParser.scss";



interface AgentTestingParserProps {
    message: string;
}

export function AgentTestingParser({message}: AgentTestingParserProps): JSX.Element {
    const [formattedText, setFormattedText] = useState<string>("");


    useEffect(() => {
        const extractors: ((text: string) => string | undefined)[] = [
            matchArrayOfStringsFormat,
            matchJsonContentMessage,
        ];

        const extracted = extractors.reduce<string | undefined>(
            (result, fn) => result ?? fn(message), undefined
        ) ?? message;

        const rich = matchRichTextFormat(extracted) ?? extracted;
        const final = linkify(rich);

        setFormattedText(final);
    }, [message]);




    function matchJsonContentMessage(text: string): string | undefined {
        try {
            const parsed = JSON.parse(text) as unknown;

            if (typeof parsed !== "object" || parsed === null) return undefined;

            const obj = parsed as Record<string, unknown>;
            const candidateKeys = ["content", "text", "response", "reply", "message", "output", "result"];

            for (const key of candidateKeys) {
                const value = obj[key];
                if (typeof value === "string" && value.trim()) {
                    return value;
                }
            }
            return undefined;
        } catch {
            return undefined;
        }
    }

    function matchArrayOfStringsFormat(text: string): string | undefined {
        try {
            const parsed = JSON.parse(text) as unknown;

            if (Array.isArray(parsed)) {
                const last = parsed[parsed.length - 1] as unknown;
                if (typeof last === "string" && last.trim()) {
                    return last.trim();
                }
            }
            return undefined;
        } catch {
            try {
                // eslint-disable-next-line no-eval -- Well, we don't have many choices with data formatted like this >.<
                const evaluated = eval(text) as unknown;

                if (Array.isArray(evaluated)) {
                    const last = evaluated[evaluated.length - 1] as unknown;
                    return typeof last === "string" && last.trim() ? last.trim() : undefined;
                }
            } catch {
                return undefined;
            }
        }
    }

    function matchRichTextFormat(text: string): string | undefined {
        if (
            !text.includes("###") &&
            !text.includes("**") &&
            !/^(?:\d+\. |- |\* )/m.test(text)
        ) {
            return undefined;
        }

        const html = text
            // Headings
           .replace(/^(?<hashes>#{2,6}) (?<content>.*)$/gm, (
                _match: string,
                _g1: string,
                _offset: number,
                _str: string,
                groups?: { hashes?: string, content?: string }
            ): string => {
                const level = groups?.hashes?.length ?? 3;
                const prefix = _offset === 0 ? "" : "<br/>";
                return `${prefix}<h${level.toString()}>${groups?.content?.trim() ?? ""}</h${level.toString()}>`;
            })
            // Bold **text**
            .replace(/\*\*(?:.*?)\*\*/g, (match) => {
                const boldText = match.slice(2, -2).trim();
                return `<strong>${boldText}</strong>`;
            })
            // Break between adjacent **bold** sections
            .replace(/(?<bold>\*\*[^*]+?\*\*)(?=[\s:;,]*\*\*)/g, (
                _match: string,
                _g1: string,
                _offset: number,
                _str: string,
                groups?: { bold?: string }
            ): string => {
                return `${groups?.bold ?? _match}<br/>`;
            })
            // Horizontal Rulers
            .replace(/^\s*-{3,}\s*$/gm, "<hr/>")
            // Numbered list items
            .replace(/^\d+\. (?:.*?)$/gm, (match) => {
                const content = match.replace(/^\d+\.\s*/, "");
                return `<li>${content}</li>`;
            })
            // Bulleted list items (- or •)
            .replace(/^\s*[-•] (?:.*?)$/gm, (match) => {
                const content = match.replace(/^\s*[-•]\s*/, "");
                return `<li>${content}</li>`;
            })
            // Group <li> items inside <ul> blocks (basic grouping)
            .replace(/(?:<li>.*?<\/li>)/gs, "<ul>$&</ul>")
            .replace(/<\/ul>\s*<ul>/g, "");

        return html;
    }


    function linkify(text: string): string {
        return text.replace(/(?:https?:\/\/|www\.)[^\s<>"')\],.]+[^\s<>"')\],.]/g, (match) => {
            const href = match.startsWith("http") ? match : `https://${match}`;
            return `<a href="${href}" target="_blank" rel="noopener noreferrer">${match}</a>`;
        });
    }



    return (
        <div className="agent-testing-parser-container">            
            <div dangerouslySetInnerHTML={{ __html: linkify(formattedText) }} />
        </div>
    );
}