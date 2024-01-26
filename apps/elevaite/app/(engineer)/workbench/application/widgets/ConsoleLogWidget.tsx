import dayjs from "dayjs";
import "./ConsoleLogWidget.scss";


const commonLabels = {
    consoleLog: "Console Log",
}


const test = [
    {
        date: dayjs().subtract(1, "h").toISOString(),
        description: "Console.ExampleFormatters.Json.Startup[0] Application started. Press Ctrl+C to shut down.Application started. Press Ctrl+C to shut down.Application started. Press Ctrl+C to shut down."
    },
    {
        date: dayjs().subtract(2, "h").toISOString(),
        description: "Console.ExampleFormatters.Json.Startup[0] Application started.Press Ctrl+C to shut down.Application started."
    },
    {
        date: dayjs().subtract(3, "h").toISOString(),
        description: "Press Ctrl+C to shut down.Application started. Press Ctrl+C to shut down.Application started. Press Ctrl+C to shut down."
    },
]


interface ConsoleLogWidgetProps {

}

export function ConsoleLogWidget(props: ConsoleLogWidgetProps): JSX.Element {
    return (
        <div className="console-log-widget-container">
            <div className="widget-label">{commonLabels.consoleLog}</div>
            <div className="log-scroller">
                <div className="log-contents">
                    {test.map((log) => <ConsoleLogEntry log={log} key={log.date} /> )}
                </div>
            </div>
        </div>
    );
}


function ConsoleLogEntry({log}: {log: {date: string, description: string}}): JSX.Element {
    return (
        <div className="console-log-container">
            <span className="time">{dayjs(log.date).format("YYYY-MM-DD hh:mm:ss")}</span>
            <span>{log.description}</span>
        </div>
    );
}