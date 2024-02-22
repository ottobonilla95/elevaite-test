import dayjs from "dayjs";
import { useEffect, useState } from "react";
import type { AppInstanceObject } from "../../../../lib/interfaces";
import { AppInstanceStatus } from "../../../../lib/interfaces";
import "./ConsoleLogWidget.scss";


const commonLabels = {
    consoleLog: "Console Log",
}

const standardizedMessages = {
    instanceStart: "Instance processing started.",
    instanceComplete: "Instance processing completed.",
    instanceFail: "Instance processing failed.",
}



interface ConsoleLogWidgetProps {
    instance?: AppInstanceObject;
}

export function ConsoleLogWidget(props: ConsoleLogWidgetProps): JSX.Element {
    const [entries, setEntries] = useState<{date: string, description: string}[]>([]);

    useEffect(() => {
        setEntries([]);
        setStandardLogEntries();
        // Get other entries?
        sortLogEntries();
    }, [props.instance]);


    function setStandardLogEntries(): void {
        if (!props.instance) return;
        if (props.instance.startTime) {
            setEntries(current => {
                if (!props.instance) return current;
                return [...current,
                    {
                        date: props.instance.startTime,
                        description: standardizedMessages.instanceStart,
                    }
                ]
            });
        }
        if (props.instance.endTime) {
            setEntries(current => {
                if (!props.instance?.endTime) return current;
                return [...current, 
                    {
                        date: props.instance.endTime,
                        description: props.instance.status === AppInstanceStatus.FAILED ? standardizedMessages.instanceFail : standardizedMessages.instanceComplete,
                    }
                ]
            });
        }
    }

    function sortLogEntries(): void {
        setEntries(current => {
            return current.sort((a, b) => { return dayjs(b.date).valueOf() - dayjs(a.date).valueOf() });
        })
    };



    return (
        <div className="console-log-widget-container">
            <div className="widget-label">{commonLabels.consoleLog}</div>
            <div className="log-scroller">
                <div className="log-contents">
                    {entries.map(entry => 
                        <ConsoleLogEntry {...entry} key={entry.date + entry.description} />
                    )}
                </div>
            </div>
        </div>
    );
}


function ConsoleLogEntry({date, description}: {date: string, description: string}): JSX.Element {
    return (
        <div className="console-log-container">
            <span className="time">{dayjs(date).format("YYYY-MM-DD hh:mm:ss")}</span>
            <span>{description}</span>
        </div>
    );
}