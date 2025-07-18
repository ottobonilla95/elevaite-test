import "./GeneratedPromptParser.scss";



interface GeneratedPromptParserProps {
    prompt?: string;
}

export function GeneratedPromptParser(props: GeneratedPromptParserProps): JSX.Element {
    return (
        <div className="generated-prompt-parser-container">
            <pre className="generated-prompt-content">
                {props.prompt}
            </pre>
        </div>
    );
}