import { ElevaiteIcons } from "@repo/ui/components";
import "./PipelineWebhook.scss";




interface PipelineWebhookProps {
    link: string;
}

export function PipelineWebhook(props: PipelineWebhookProps): JSX.Element {
    return (
        <div className="pipeline-webhook-container">
            <span>Webhook:</span>
            <a href={props.link} target="_blank" rel="noreferrer" title={props.link}>
                <span className="link">{props.link}</span>
                <ElevaiteIcons.SVGOpenLink/>
            </a>
        </div>
    );
}