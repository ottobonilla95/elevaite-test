import { ElevaiteIcons } from "@repo/ui/components";
import { ExtractionStatus, MatchingStatus } from "src/interfaces";




interface StatusIconProps {
    status: ExtractionStatus | MatchingStatus;
}

export function StatusIcon(props: StatusIconProps): JSX.Element {
    switch (props.status) {
        case ExtractionStatus.Uploading: return <div className="status-icon-container"><ElevaiteIcons.SVGUpload /></div>
        case ExtractionStatus.Extracting: return <div className="status-icon-container highlight"><ElevaiteIcons.SVGInstanceProgress /></div>
        case ExtractionStatus.Failed: return <div className="status-icon-container danger"><ElevaiteIcons.SVGXmark /></div>
        case ExtractionStatus.Complete: return <div className="status-icon-container blue"><ElevaiteIcons.SVGCheckmark /></div>
        case MatchingStatus.Found: return <div className="status-icon-container success"><ElevaiteIcons.SVGCheckmark /></div>
        case MatchingStatus.Failed: return <div className="status-icon-container"><ElevaiteIcons.SVGQuestionMark /></div>
    }
}