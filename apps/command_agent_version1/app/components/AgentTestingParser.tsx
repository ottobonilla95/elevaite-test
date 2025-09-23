// Clean, component-based rendering with interleaved HTML + <CodeBlockParser />
import { useEffect, useState } from "react";
import "./AgentTestingParser.scss";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";


type InterleavedPart =
  | { kind: "html"; html: string }
  | { kind: "code"; block: CodeBlockToken };
interface CodeBlockToken { token: string; lang?: string; code: string }
interface ListStructure { type: "ul" | "ol"; indent: number; liOpen: boolean }

interface AgentTestingParserProps {
  message: string;
  isUser?: boolean;
  isError?: boolean;
}



export function AgentTestingParser({ message, isUser, isError }: AgentTestingParserProps): JSX.Element {
  const [parts, setParts] = useState<InterleavedPart[]>([]);
  const [expanded, setExpanded] = useState(false);

  const isUserLong = Boolean(isUser) && (message.split(/\r?\n/).length > 5);

  useEffect(() => {
    // console.log("Raw message", message);
    const extractors: ((text: string) => string | undefined)[] = [
      matchArrayOfStringsFormat,
      matchJsonContentMessage,
    ];

    const extracted = extractors.reduce<string | undefined>(
      (result, fn) => result ?? fn(message), undefined
    ) ?? message;

    const masked = maskCodeFencesReact(extracted);
    const safe = escapeHtml(masked.text);
    const rich = matchRichTextFormat(safe) ?? safe;
    const linked = linkify(rich);
    const interleaved = splitHtmlByTokens(linked, masked.blocks);

    setParts(interleaved);
  }, [message]);

  return (
    <div className="agent-testing-parser-container">
        <div className={[
            "parsed-text",
            isError ? "parser-error" : undefined,
            isUserLong && !expanded ? "is-clamped" : undefined
        ].filter(Boolean).join(" ")}>
            {!isError ? undefined : 
                <div className="error-header">Error encountered:</div>
            }
            {renderInterleaved(parts)}
        </div>

      {!isUserLong ? undefined : (
        <div className="parser-button-container">
          <CommonButton
            className={["parser-expand-btn", expanded ? "expanded" : undefined].filter(Boolean).join(" ")}
            noBackground
            onClick={() => { setExpanded(v => !v); }}
          >
            <ElevaiteIcons.SVGChevron type="down" />
          </CommonButton>
        </div>
      )}
    </div>
  );
}






    function matchJsonContentMessage(text: string): string | undefined {
        try {
            const parsed = JSON.parse(text) as unknown;
            if (typeof parsed !== "object" || parsed === null) return undefined;

            const obj = parsed as Record<string, unknown>;
            const candidateKeys = ["content", "text", "response", "reply", "message", "output", "result"];
            for (const key of candidateKeys) {
            const value = obj[key];
            if (typeof value === "string" && value.trim()) return value;
            }
            return undefined;
        } catch {
            return undefined;
        }
    }

    function matchArrayOfStringsFormat(text: string): string | undefined {
        try {
            const parsed: unknown = JSON.parse(text);
            if (Array.isArray(parsed)) {
                const parsedArray = parsed as unknown[];
                const last = parsedArray.length > 0 ? parsedArray[parsedArray.length - 1] : undefined;
                if (typeof last === "string") {
                    const trimmed = last.trim();
                    return trimmed ? trimmed : undefined;
                }
            }
        } catch {
            // no-op
        }

        // Permissive fallback for array-like payloads: ["a","b"] or ['a','b'] (whitespace allowed)
        const arrayLikePattern = /^\s*\s*(?:(?:"[^"]*"|'[^']*')(?:\s*,\s*(?:"[^"]*"|'[^']*'))*)?\s*\s*$/s;
        if (!arrayLikePattern.test(text)) return undefined;

        // Extract quoted string tokens (supports basic escapes) using a named group to satisfy lint
        const tokenPattern = /(?:"(?<contentDouble>[^"\\]*(?:\\.[^"\\]*)*)"|'(?<contentSingle>[^'\\]*(?:\\.[^'\\]*)*)')/g;

        const tokens: string[] = [];
        for (const m of text.matchAll(tokenPattern)) {
            const match = m as RegExpMatchArray;
            const content: string = match[1] || match[2] || "";
            tokens.push(content);
        }

        if (tokens.length === 0) return undefined;

        const last = tokens[tokens.length - 1];
        const trimmed = last.trim();
        return trimmed ? trimmed : undefined;
    }


    function maskCodeFencesReact(src: string): { text: string; blocks: CodeBlockToken[] } {
        const blocks: CodeBlockToken[] = [];
        const fenceRe = /(?<prefix>^|\n)(?<fence>```|~~~)(?<lang>[a-zA-Z0-9+_-]*)[ \t]*\n(?<code>[\s\S]*?)(?:\n\k<fence>)(?=(?:\n|$))/g;

        let index = 0;

        const text = src.replace(fenceRe, (_m, prefix: string, ...rest: unknown[]) => {
            const groups = rest[rest.length - 1] as { fence?: string; lang?: string; code?: string };
            const lang = (groups.lang ?? "").trim() || undefined;
            const body = (groups.code ?? "").replace(/\n$/, "");
            const token = `\uE000CODE_${(index++).toString()}\uE000`;
            blocks.push({ token, lang, code: body });
            return `${prefix}${token}`;
        });

        return { text, blocks };
    }

    function splitHtmlByTokens(html: string, blocks: CodeBlockToken[]): InterleavedPart[] {
        if (!blocks.length) return [{ kind: "html", html }];

        let cursor = 0;
        const parts: InterleavedPart[] = [];

        const ordered = [...blocks]
            .map(b => ({ block: b, idx: html.indexOf(b.token) }))
            .filter(x => x.idx !== -1)
            .sort((a, b) => a.idx - b.idx);

        for (const { block, idx } of ordered) {
            if (idx > cursor) {
            parts.push({ kind: "html", html: html.slice(cursor, idx) });
            }
            parts.push({ kind: "code", block });
            cursor = idx + block.token.length;
        }

        if (cursor < html.length) {
            parts.push({ kind: "html", html: html.slice(cursor) });
        }

        return parts;
    }

    function renderInterleaved(parts: InterleavedPart[]): JSX.Element[] {
        let keySeq = 0;
        return parts.map((p) => {
            if (p.kind === "html") {
            return <div key={`h-${(keySeq++).toString()}`} dangerouslySetInnerHTML={{ __html: p.html }} />;
            }
            return <CodeBlockParser key={`c-${(keySeq++).toString()}`} lang={p.block.lang} code={p.block.code} />;
        });
    }

    function matchRichTextFormat(text: string): string | undefined {
        // early-out if nothing markdowny present
        if (!(/#{2,6}\s|[*]{2}|^\s*[-•]\s|\d+\.\s|`/.test(text))) return undefined;

        // 1) Inline transforms first (safe: we escape outside code blocks earlier)
        let formattedResult = text
            // inline code: `code`
            .replace(/`(?<inline>[^`\n]+)`/g, (_m, _g1, _off, _str, g?: { inline?: string }) =>
            `<code class="inline-code">${g?.inline ?? ""}</code>`
            )
            // headings: ##..###### <text>
            .replace(/^(?<hashes>#{2,6}) (?<content>.*)$/gm, (m: string) => {
            const r = /^(?<hashes>#{2,6}) (?<content>.*)$/.exec(m);
            if (!r?.groups) return m;
            const level = r.groups.hashes.length.toString();
            return `<h${level}>${r.groups.content.trim()}</h${level}>`;
            })
            // bold: **text**
            .replace(/\*\*(?<b>.+?)\*\*/g, (_m, _g1, _off, _str, g?: { b?: string }) =>
            `<strong>${(g?.b ?? "").trim()}</strong>`
            )
            // horizontal rule
            .replace(/^\s*-{3,}\s*$/gm, "<hr/>");

        // 2) Block-level list rendering (ordered + unordered, with simple nesting)
        formattedResult = renderLists(formattedResult);

        return formattedResult;
    }

    function renderLists(src: string): string {
        const lines = src.split(/\r?\n/);
        let out = "";
        const stack: ListStructure[] = [];

        function closeLi(): void {
            if (stack.length && stack[stack.length - 1].liOpen) {
            out += "</li>";
            stack[stack.length - 1].liOpen = false;
            }
        }
        function openList(type: "ul" | "ol", indent: number): void {
            out += type === "ul" ? "<ul>" : "<ol>";
            stack.push({ type, indent, liOpen: false });
        }
        function closeList(): void {
            const ctx = stack.pop();
            if (!ctx) return;
            if (ctx.liOpen) out += "</li>";
            out += ctx.type === "ul" ? "</ul>" : "</ol>";
        }
        function unwindTo(targetIndent: number): void {
            while (stack.length && stack[stack.length - 1].indent > targetIndent) {
            closeList();
            }
        }

        for (let i = 0; i < lines.length; i++) {
            const raw = lines[i];
            const line = raw; // already escaped/inline-processed upstream
            const m = /^(?<spaces>\s*)(?:(?<num>\d+)\.\s+(?<o>.+)|(?<bullet>[-•])\s+(?<u>.+))$/.exec(line);

            if (m?.groups) {
                const indent = (m.groups.spaces).length;
                const isOrdered = Boolean(m.groups.num);
                let content = isOrdered ? m.groups.o : m.groups.u;
                const type: "ul" | "ol" = isOrdered ? "ol" : "ul";

                if (!stack.length) {
                openList(type, indent);
                } else {
                if (stack[stack.length - 1].indent > indent) unwindTo(indent);
                if (!stack.length || stack[stack.length - 1].indent < indent) {
                    openList(type, indent);
                } else if (stack[stack.length - 1].type !== type) {
                    closeList();
                    openList(type, indent);
                }
                }

                // ensure no literal "1. " leaks into content
                if (isOrdered) content = content.replace(/^\d+\.\s*/, "");

                closeLi();
                stack[stack.length - 1].liOpen = true;
                out += `<li>${content}`;
            } else if (raw.trim() === "") {
                // look ahead: if the next non-empty line starts a list, keep the current list open
                let j = i + 1;
                let nextNonEmpty: string | undefined;
                while (j < lines.length && (nextNonEmpty = lines[j]) !== undefined && nextNonEmpty.trim() === "") j++;
                const nextIsList = Boolean(nextNonEmpty && /^(?<spaces>\s*)(?:(?<num>\d+)\.\s+.+|(?<bullet>[-•])\s+.+)$/.test(nextNonEmpty));

                if (stack.length) {
                if (nextIsList) {
                    // end current <li>, keep list(s) open
                    closeLi();
                    out += "\n";
                } else {
                    // end all lists
                    while (stack.length) closeList();
                    out += "\n";
                }
                } else {
                out += "\n";
                }
            } else if (stack.length) {
                out += `<br/>${line}`;
            } else {
                out += `${line}\n`;
            }
        }

        // close any remaining lists
        while (stack.length) closeList();
        return out;
    }


    function linkify(text: string): string {
        let html = text.replace(/\[(?<linkText>[^\]]+)\]\((?<url>https?:\/\/[^\s)]+)\)/g,
            (_m, ...args) => {
            const groups = args[args.length - 1] as { linkText: string; url: string };
            return `<a href="${groups.url}" title="${groups.url}" target="_blank" rel="noopener noreferrer">${groups.linkText}</a>`;
            }
        );

        html = html.replace(/(?<prefix>^|[^"'>])(?<url>https?:\/\/[^\s<>"'[\]()]+)/g,
            (_m, ...args) => {
            const groups = args[args.length - 1] as { prefix: string; url: string };
            return `${groups.prefix}<a href="${groups.url}" target="_blank" rel="noopener noreferrer">${groups.url}</a>`;
            }
        );

        return html;
    }

    function escapeHtml(text: string): string {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }







export function CodeBlockParser(props: { lang?: string; code: string }): JSX.Element {
  const { lang, code } = props;
  const [copied, setCopied] = useState(false);

  function onCopy(): void {
    void navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      window.setTimeout(() => { setCopied(false); }, 1500);
    });
  }

  return (
    <div className="code-block-container">
        <div className="code-block-header">
            <CommonButton
                className={["code-copy-button", copied ? "copied" : undefined].filter(Boolean).join(" ")}                
                onClick={onCopy}
                noBackground
            >
                {copied ? <ElevaiteIcons.SVGCheckmark/> : <ElevaiteIcons.SVGCopy/> }
                {copied ? "Copied!" : "Copy code" }
            </CommonButton>
        </div>

        <pre className="code-block">
            <code className={lang ? `language-${lang}` : undefined}>{code}</code>
        </pre>
    </div>
  );
}
