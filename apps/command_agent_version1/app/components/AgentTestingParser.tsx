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
           .replace(/^(#{2,6}) (.*)$/gm, (match, hashes, content) => {
                console.log("🔍 Heading match:", { match, hashes, content });
                const level = hashes.length;
                const prefix = match.indexOf(hashes) === 0 ? "" : "<br/>";
                return `${prefix}<h${level}>${content.trim()}</h${level}>`;
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
        // Convert markdown-style links first
        let html = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
            '<a href="$2" title="$2" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        // Then linkify any remaining plain URLs - FIXED to capture full URLs including dots
        html = html.replace(/(^|[^"'>])(https?:\/\/[^\s<>"'\[\]()]+)/g,
            '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>'
        );

        return html;

        // OLD CODE (commented out):
        // Original problematic URL regex that was cutting off URLs at dots:
        // html = html.replace(/(?<!["'>])\b(?<url>https?:\/\/[^\s<>"')\],.]+[^\s<>"')\],.])/g, (
        //     _match, _p1, _offset, _string, groups: { label?: string; url?: string }
        // ) => {
        //     if (!groups.url) return _match;
        //     return `<a href="${groups.url}" target="_blank" rel="noopener noreferrer">${groups.url}</a>`;
        // });
    }



    return (
        <div className="agent-testing-parser-container">
            <div dangerouslySetInnerHTML={{ __html: formattedText }} />
        </div>
    );
}