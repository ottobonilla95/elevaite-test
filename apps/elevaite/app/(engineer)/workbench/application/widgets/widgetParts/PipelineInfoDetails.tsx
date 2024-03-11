import { getDisplayValueFromStepDetail } from "../../../../../lib/helpers";
import type { AppInstanceObject, ApplicationType, PipelineStep, PipelineStepAddedInfo, PipelineStepData } from "../../../../../lib/interfaces";
import "./PipelineInfoDetails.scss";



interface PipelineInfoDetailsProps {
    data?: PipelineStepAddedInfo[];
    selectedInstance?: AppInstanceObject;
    selectedStep?: PipelineStep & PipelineStepData;
    type?: ApplicationType;
};

export function PipelineInfoDetails(props: PipelineInfoDetailsProps): JSX.Element {
    return (
        <div className="pipeline-info-details-container">
            {!props.data ? null : props.data.map(item => 
                <div className="pipeline-info-item" key={item.label}>
                    <span className="label">{item.label}:</span>
                    <span className="text" title={getDisplayValueFromStepDetail(item, props.selectedStep, props.selectedInstance, props.type)}>                        
                        {getDisplayValueFromStepDetail(item, props.selectedStep, props.selectedInstance, props.type)}
                    </span>
                </div>
            )}
        </div>
    );
}