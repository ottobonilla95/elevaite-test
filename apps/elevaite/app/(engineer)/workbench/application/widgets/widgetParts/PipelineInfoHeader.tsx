import "./PipelineInfoHeader.scss";



interface PipelineInfoHeaderProps {
    title: string;
    step?: string;
    children?: React.ReactNode;
}

export function PipelineInfoHeader(props: PipelineInfoHeaderProps): JSX.Element {
    return (
        <div className="pipeline-info-header-container">

            <div className="title-row">
                <span>{props.title}</span>
                {props.children}
            </div>

            <span>{props.step ? `${props.step} — Details` : ""}</span>

        </div>
    );
}