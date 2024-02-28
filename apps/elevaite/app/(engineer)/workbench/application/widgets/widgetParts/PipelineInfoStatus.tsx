import { ElevaiteIcons } from "@repo/ui/components";
import { PipelineStatus } from "../../../../../lib/interfaces";
import "./PipelineInfoStatus.scss";



interface PipelineInfoStatusProps {
    status?: PipelineStatus;
}

export function PipelineInfoStatus(props: PipelineInfoStatusProps): JSX.Element {

    function getClassName(status?: PipelineStatus): string {        
        switch (status) {
            case PipelineStatus.IDLE: return "starting";
            case PipelineStatus.RUNNING: return "running";
            case PipelineStatus.COMPLETED: return "completed";
            case PipelineStatus.FAILED: return "failed";
            default: return "";
        }
    }

    function getIcon(status?: PipelineStatus): React.ReactNode {
        switch (status) {
            case PipelineStatus.IDLE: return <ElevaiteIcons.SVGTarget className="pipeline-info-icon starting" />
            case PipelineStatus.RUNNING: return <ElevaiteIcons.SVGInstanceProgress className="pipeline-info-icon running" />
            case PipelineStatus.COMPLETED: return <ElevaiteIcons.SVGCheckmark className="pipeline-info-icon completed" />
            case PipelineStatus.FAILED: return <ElevaiteIcons.SVGWarning className="pipeline-info-icon failed" />
            default: return null;
        }
    }
    function getLabel(status?: PipelineStatus): string {
        switch (status) {
            case PipelineStatus.IDLE: return "Initializing";
            case PipelineStatus.RUNNING: return "In Progress";
            case PipelineStatus.COMPLETED: return "Complete";
            case PipelineStatus.FAILED: return "Failed";
            default: return "";
        }
    }  

    return (
        <div className="pipeline-info-status-container">
            <div className={["content", getClassName(props.status)].filter(Boolean).join(" ")}>
                {getIcon(props.status)}
                <span>{getLabel(props.status)}</span>
            </div>
            <div className={["backdrop", getClassName(props.status)].filter(Boolean).join(" ")}/>
        </div>
    );
}