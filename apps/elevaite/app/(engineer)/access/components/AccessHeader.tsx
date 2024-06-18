"use client"
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./AccessHeader.scss";




export function AccessHeader(): JSX.Element {

    function handleAccessRefresh(): void {
        console.log("Refreshing actions");
    }


    return (
        <div className="access-header-container">
            <div className="part-container left">
                <div className="title">ACCESS MANAGEMENT</div>
            </div>

            <div className="part-container right">
                <CommonButton
                    className="refresh-button"
                    onClick={handleAccessRefresh}
                    noBackground
                >
                    <ElevaiteIcons.SVGRefresh/>
                </CommonButton>
            </div>
        </div>
    );
}