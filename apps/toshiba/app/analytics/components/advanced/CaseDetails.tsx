import "./CaseDetails.scss";




const testData = {
    title: "Motion Detection Delay Issue Post-Firmware Update",
    details: [
        { label: "ACCT918394B", tooltip: "Reference Number" },
        { label: "Today at 1:00 PM", tooltip: "Latest Update" },
        { label: "10 MIN", tooltip: "Chat Duration" },
    ]
}



export function CaseDetails(): JSX.Element {

    return (
        <div className="case-details-container">
            <span className="title" title={testData.title}>{testData.title}</span>
            <div className="details-scroller">
                <div className="details-contents">
                    {testData.details.map(detail =>
                        <div
                            key={detail.label}
                            className="detail"
                            title={detail.tooltip ?? ""}
                        >
                            {detail.label}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}