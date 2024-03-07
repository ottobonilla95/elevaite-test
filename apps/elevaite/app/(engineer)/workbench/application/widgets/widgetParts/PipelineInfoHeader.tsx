import "./PipelineInfoHeader.scss";



interface PipelineInfoHeaderProps {
    title?: string;
    step?: string;
    children?: React.ReactNode;
}

export function PipelineInfoHeader(props: PipelineInfoHeaderProps): JSX.Element {
    return (
        <div className="pipeline-info-header-container">

            <div className="title-row">
                <span>{props.title ? props.title : "Select Step"}</span>
                {props.children}
            </div>

            <span>{!props.title ? "to see details" : props.step ? `${props.step} — Details` : ""}</span>

        </div>
    );
}