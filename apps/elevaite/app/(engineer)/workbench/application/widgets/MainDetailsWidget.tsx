import dayjs from "dayjs";
import { useElapsedTime } from "@repo/ui/hooks";
import "./MainDetailsWidget.scss"
import type { AppInstanceObject } from "../../../../lib/interfaces";




interface MainDetailsWidgetProps {
    instance: AppInstanceObject | undefined;
}


export default function MainDetailsWidget({instance}: MainDetailsWidgetProps): JSX.Element {

    return (
        <div className={[
            "main-details-widget-container",
            !instance ? "inert" : undefined,
        ].filter(Boolean).join(" ")}>
            
            <div className="main-details-text">
                <div className="dataset">{instance ? `Dataset Created: ${instance.datasetId ?? "None"}` : ""}</div>
                <div className="creator">{instance ? `Created by: ${instance.creator}` : ""}</div>
            </div>

            <div className="main-details-separator"/>

            <div className="main-details-time">
                <div className="elapsed-time-container">
                    <ElapsedTimeDisplay endTime={instance?.endTime} startTime={instance?.startTime} />
                </div>
                <div className="start-datetime">
                    <span className="start-date">{instance ? dayjs(instance.startTime).format("MMM DD, YYYY") : "Month dd, yyyy"}</span>
                    <span className="start-time">{instance ? dayjs(instance.startTime).format("hh:mm a") : "hh:mm"}</span>
                </div>
            </div>

        </div>
    );
}




function ElapsedTimeDisplay({startTime, endTime}: {startTime?: string | undefined, endTime?: string | undefined}): JSX.Element {
    const elapsedTime = useElapsedTime(startTime ? startTime : "", endTime);

    return (
        <div className={[
            "elapsed-time-display-container",
            startTime ? undefined : "inert",
        ].filter(Boolean).join(" ")}>
            <span className="digit">{startTime ? elapsedTime.elapsedDays : "-"}</span>
            <span className="digit-label">{!startTime || elapsedTime.elapsedDays ? "d" : undefined}</span>
            <span className="digit">{startTime ? elapsedTime.elapsedHours : "-"}</span>
            <span className="digit-label">{!startTime || elapsedTime.elapsedHours ? "h" : undefined}</span>
            <span className="digit">{startTime ? elapsedTime.elapsedMinutes : "-"}</span>
            <span className="digit-label">{!startTime || elapsedTime.elapsedMinutes ? "m" : undefined}</span>
            <span className="digit">{startTime ? elapsedTime.elapsedSeconds : "-"}</span>
            <span className="digit-label">{!startTime || elapsedTime.elapsedSeconds ? "s" : undefined}</span>
        </div>
    );
}