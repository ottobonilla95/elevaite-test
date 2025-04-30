import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { useState } from "react";
import "./CoPilot.scss";
import { UploadTranscript } from "./UploadTranscript";



interface CoPilotProps {
    label?: string;
    noUpload?: boolean;
    children?: React.ReactNode | React.ReactNode[];
}

export function CoPilot(props: CoPilotProps): JSX.Element {
    const [isUploadOpen, setIsUploadOpen] = useState(false);


    function handleUploadTranscriptClick(): void {
        setIsUploadOpen(true);
    }


    return (
        <div className="co-pilot-container">

            <div className="co-pilot-header">
                <span>{props.label ?? "CoPilot"}</span>
                {props.noUpload ? undefined : undefined
                    // <CommonButton
                    //     className="upload-button"
                    //     onClick={handleUploadTranscriptClick}
                    // >
                    //     <ElevaiteIcons.SVGUpload/>
                    //     Upload Transcript
                    // </CommonButton>
                }
            </div>

            <div className="co-pilot-main">

                {props.children}

            </div>


            {!isUploadOpen ? undefined :
                <CommonModal
                    onClose={() => { setIsUploadOpen(false); }}
                >
                    <UploadTranscript/>
                </CommonModal>
            }
        </div>
    );
}