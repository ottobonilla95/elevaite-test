import "./PipelineInfoDetails.scss";



interface PipelineInfoDetailsProps {
    data?: {
        label: string,
        text: string
    }[];
};

export function PipelineInfoDetails(props: PipelineInfoDetailsProps): JSX.Element {
    return (
        <div className="pipeline-info-details-container">
            {!props.data ? null : props.data.map(item => 
                <div className="pipeline-info-item" key={item.label}>
                    <span className="label">{item.label}</span>
                    <span className="text" title={item.text}>{item.text}</span>
                </div>
            )}
        </div>
    );
}