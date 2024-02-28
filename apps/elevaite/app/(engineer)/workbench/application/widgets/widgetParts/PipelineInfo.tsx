import { PipelineStatus } from "../../../../../lib/interfaces";
import { PipelineDataLake } from "./PipelineDataLake";
import "./PipelineInfo.scss";
import { PipelineInfoDetails } from "./PipelineInfoDetails";
import { PipelineInfoHeader } from "./PipelineInfoHeader";
import { PipelineInfoStatus } from "./PipelineInfoStatus";
import { PipelineWebhook } from "./PipelineWebhook";


const TEST_DETAILS = [
    {label: "Step Started:", text: "time"},
    {label: "Step Ended:", text: "another time"},
    {label: "Another item:", text: "just another item"},
];


interface PipelineInfoProps {
    
}

export function PipelineInfo(props: PipelineInfoProps): JSX.Element {
    return (
        <div className="pipeline-info-container">

            <PipelineInfoHeader
                title="Worker Progress"
                step="Step 1"
            >
                <PipelineInfoStatus status={PipelineStatus.IDLE} />
            </PipelineInfoHeader>

            <PipelineInfoDetails data={TEST_DETAILS} />            

            <PipelineWebhook link="https://elevaite-s3docingest.com" />

            <PipelineDataLake />

        </div>
    );
}