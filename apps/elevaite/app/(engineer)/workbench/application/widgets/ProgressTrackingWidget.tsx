"use client";
import { useEffect, useState } from "react";
import { AppInstanceObject, ChartDataObject } from "../../../../lib/interfaces";
import "./ProgressTrackingWidget.scss";
import { getInstanceChartData } from "../../../../lib/actions";



enum ProgressBitTypes {
    docsIngested = "Docs Ingested",
    averageDocSize = "Avg Doc Size",
    totalPages = "Total Pages",
    totalChukns = "Total Chunks",
    dataLoading = "Data Loading Progress",
}

const progressBits = [
    {   label: ProgressBitTypes.docsIngested,
        units: "files",
        value: 0,     },
    {   label: ProgressBitTypes.averageDocSize,
        units: "KB",
        value: 0,     },
    // {   label: ProgressBitTypes.totalPages,
    //     units: "pp.",
    //     value: 0,     },
    // {   label: ProgressBitTypes.totalChukns,
    //     units: "chunks",
    //     value: 0,     },
    {   label: ProgressBitTypes.dataLoading,
        units: "Completion",
        value: 0,     },
];



interface ProgressTrackingWidgetProps {
    applicationId: string | null;
    instance: AppInstanceObject;
}

export function ProgressTrackingWidget(props: ProgressTrackingWidgetProps): JSX.Element {
    const [chartData, setChartData] = useState<ChartDataObject>();
    const [displayBits, setDisplayBits] = useState(progressBits);



    useEffect(() => {
        if (!props.instance) return;
        if (props.instance.chartData) setChartData(props.instance.chartData);
        else fetchChartData();
        const interval = setInterval(() => {
            fetchChartData();
        }, 10000);
        return () => {clearInterval(interval)};
    }, [props.instance]);


    useEffect(() => {
        const modifiedBits = structuredClone(displayBits);

        // docs ingested
        const docsIngested = modifiedBits.find(item => item.label === ProgressBitTypes.docsIngested);
        if (docsIngested) docsIngested.value = chartData?.ingestedItems ?? 0;
        // average doc size
        const avgSize = modifiedBits.find(item => item.label === ProgressBitTypes.averageDocSize);
        if (avgSize) avgSize.value = Math.round(chartData ? chartData.totalSize / chartData.totalItems : 0);
        // progress
        const loadingProgress = modifiedBits.find(item => item.label === ProgressBitTypes.dataLoading);
        if (loadingProgress) loadingProgress.value = Math.round(chartData ? chartData.ingestedSize / chartData.totalSize * 100 : 0);

        setDisplayBits(modifiedBits);
    }, [chartData]);



    async function fetchChartData() {
        if (!props.applicationId || !props.instance) return;
        try {
            const fetchedData = await getInstanceChartData(props.applicationId, props.instance.id);
            if (fetchedData) setChartData(fetchedData);
        } catch (error) {
            console.error('Error fetching chart data:', error);
        }
    }



    return (
        <div className="progress-tracking-widget-container">
            {displayBits.map(bit => <ProgressBit {...bit} key={bit.label} />)}
        </div>
    );
}




function ProgressBit(props: {label: string, units: string, value: number}): JSX.Element {
    return (
        <div className={["progress-bit-container", props.label === ProgressBitTypes.dataLoading ? "loading-bar-version" : undefined].filter(Boolean).join(" ")}>
            <div className="bit-label">{props.label}</div>
            {props.label === ProgressBitTypes.dataLoading ? 
                <div className="loading-bar-container">
                    <div className="loading-bar-content">
                        <div className="bit-value">{props.value}%</div>
                        <div className="bit-units">{props.units}</div>
                    </div>
                    <div className="loading-bar">
                        <div className="fill-bar" style={{width: `${props.value}%`}} />
                    </div>
                </div>
            :
                <div className="bit-content">
                    <div className="bit-value">{props.value}</div>
                    <div className="bit-units">{props.units}</div>
                </div>
            }
        </div>
    );
}