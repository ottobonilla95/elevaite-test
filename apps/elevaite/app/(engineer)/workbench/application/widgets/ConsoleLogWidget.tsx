import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { getInstanceLogData } from "../../../../lib/actions/applicationActions";
import type { AppInstanceLogObject, AppInstanceObject } from "../../../../lib/interfaces";
import { AppInstanceLogLevel, AppInstanceStatus } from "../../../../lib/interfaces";
import "./ConsoleLogWidget.scss";


const commonLabels = {
    consoleLog: "Console Log",
    loading: "Loading. Please wait...",
    emptyLog: "The log is empty.",
};

const standardizedMessages = {
    instanceStart: "Instance processing started.",
    instanceComplete: "Instance processing completed.",
    instanceFail: "Instance processing failed.",
};

interface ConsoleLogWidgetProps {
    applicationId: string | null;
    instance?: AppInstanceObject;
}

export function ConsoleLogWidget(props: ConsoleLogWidgetProps): JSX.Element {
    const [isClosed, setIsClosed] = useState(false);
    const [entries, setEntries] = useState<AppInstanceLogObject[]>([]);
    const [loading, setLoading] = useState(false);


    useEffect(() => {
        setEntries([]);
        if (!props.applicationId || !props.instance) return;
        void fetchInstanceLog(props.applicationId, props.instance.id);
    }, [props.instance]);

 
    async function fetchInstanceLog(appId: string, instanceId: string): Promise<void> {
        try {
            setLoading(true);
            const fetchedLog = await getInstanceLogData(appId, instanceId);
            if (fetchedLog.length > 0) {
                setEntries(sortLogEntries(fetchedLog));
            } else {
                setStandardLogEntries();
            }
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching instance log:", error);
        } finally {
            setLoading(false);
        }
    }


    function setStandardLogEntries(): void {
        if (!props.instance) return;
        if (props.instance.startTime) {
            setEntries((current) => {
                if (!props.instance) return sortLogEntries(current);
                return sortLogEntries([
                    ...current,
                    {
                        timestamp: props.instance.startTime,
                        message: standardizedMessages.instanceStart,
                        level: AppInstanceLogLevel.INFO,
                    },
                ]);
            });
        }
        if (props.instance.endTime) {
            setEntries((current) => {
                if (!props.instance?.endTime) return sortLogEntries(current);
                return sortLogEntries([
                    ...current,
                    {
                        timestamp: props.instance.endTime,
                        message: props.instance.status === AppInstanceStatus.FAILED ? standardizedMessages.instanceFail : standardizedMessages.instanceComplete,
                        level: AppInstanceLogLevel.INFO,
                    }
                ]);
            });
        }
    }

    function sortLogEntries(logs: AppInstanceLogObject[]): AppInstanceLogObject[] {
        return logs.sort((a, b) => {
            return dayjs(b.timestamp).valueOf() - dayjs(a.timestamp).valueOf();
        });
    }

    return (
        <div className="console-log-widget-container">
            <div className="console-log-header">                
                <div className="widget-label">{commonLabels.consoleLog}</div>
                <CommonButton
                    className={["console-log-accordion-button", isClosed ? "closed" : undefined].filter(Boolean).join(" ")}
                    onClick={() => {
                        setIsClosed((currentValue) => !currentValue);
                    }}
                >
                    <ElevaiteIcons.SVGChevron />
                </CommonButton>
            </div>

            
            <div className={["console-log-accordion", isClosed ? "closed" : undefined].filter(Boolean).join(" ")}>
                <div className="console-log-content">
                    <div className="separator" />

                    <div className="log-scroller">
                        <div className="log-contents">
                            {loading ? 
                                <div className="loading"><ElevaiteIcons.SVGSpinner/><span>{commonLabels.loading}</span></div>
                                : entries.length === 0 ? 
                                <div className="no-entries">{commonLabels.emptyLog}</div>
                                :
                                entries.map((entry) => (
                                    <ConsoleLogEntry {...entry} key={entry.timestamp + entry.message} />
                                ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function ConsoleLogEntry({ timestamp, message, level }: AppInstanceLogObject): JSX.Element {
    return (
        <div className={["console-log-container", level].join(" ")}>
            <span className="time">{dayjs(timestamp).format("YYYY-MM-DD hh:mm:ss")}</span>
            <span>{message}</span>
        </div>
    );
}
