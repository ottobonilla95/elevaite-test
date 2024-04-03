"use client";
import { ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { getInstanceChartData } from "../../../../lib/actions/applicationActions";
import type { AppInstanceObject, ChartDataObject } from "../../../../lib/interfaces";
import { AppInstanceStatus } from "../../../../lib/interfaces";
import "./ProgressTrackingWidgetOld.scss";

enum ProgressBitTypes {
    DocsIngested = "Docs Ingested",
    AverageDocSize = "Avg Doc Size",
    TotalPages = "Total Pages",
    TotalChukns = "Total Chunks",
    DataLoading = "Data Loading Progress",
}

const progressBits = [
    {   label: ProgressBitTypes.DocsIngested,
        units: "files",
        value: -1,     },
    {   label: ProgressBitTypes.AverageDocSize,
        units: "KB",
        value: -1,     },
    // {   label: ProgressBitTypes.TotalPages,
    //     units: "pp.",
    //     value: -1,     },
    // {   label: ProgressBitTypes.TotalChukns,
    //     units: "chunks",
    //     value: -1,     },
    {   label: ProgressBitTypes.DataLoading,
        units: "Completion",
        value: -1,     },
];

interface ProgressTrackingWidgetProps {
    applicationId: string | null;
    instance?: AppInstanceObject;
}

export function ProgressTrackingWidget(props: ProgressTrackingWidgetProps): JSX.Element {
    const [chartData, setChartData] = useState<ChartDataObject>();
    const [displayBits, setDisplayBits] = useState(progressBits);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        setIsLoading(true);
    }, [props.applicationId, props.instance]);

    useEffect(() => {
        if (!props.instance) return;
        if (props.instance.chartData) setChartData(props.instance.chartData);
        if (props.instance.status === AppInstanceStatus.RUNNING) {
            void fetchChartData();
            const interval = setInterval(() => {
                void fetchChartData();
            }, 5000);
            return () => {clearInterval(interval)};
        }
        setIsLoading(false);
    }, [props.instance]);

    useEffect(() => {
        if (!chartData) return;
        const modifiedBits = structuredClone(displayBits);

        // docs ingested
        const docsIngested = modifiedBits.find(item => item.label === ProgressBitTypes.DocsIngested);
        if (docsIngested) docsIngested.value = chartData.ingestedItems;
        // average doc size
        const avgSize = modifiedBits.find(item => item.label === ProgressBitTypes.AverageDocSize);
        if (avgSize) avgSize.value = Math.round(chartData.totalItems > 0 ? (chartData.totalSize / chartData.totalItems / 1024) : 0);
        // progress
        const loadingProgress = modifiedBits.find(item => item.label === ProgressBitTypes.DataLoading);
        if (loadingProgress) loadingProgress.value = Math.round(chartData.totalSize > 0 ? (chartData.ingestedSize / chartData.totalSize * 100) : 0);

        setDisplayBits(modifiedBits);
    }, [chartData]);

    async function fetchChartData(): Promise<void> {
        if (!props.instance || !props.applicationId) return;
        try {
            const fetchedData = await getInstanceChartData(props.applicationId, props.instance.id);
            setChartData(fetchedData);
        } catch (error) {
            // console.error('Error fetching chart data:', error);
        } finally {
            // Only do this once when initiating. We don't want it to show on subsequent loads.
            setIsLoading(false);
        }
    }

    return (
        <div className="progress-tracking-widget-container">
            {displayBits.map((bit) => (
                <ProgressBit
                    key={bit.label}
                    {...bit}
                    isLoading={isLoading}
                    disabled={props.instance?.status === AppInstanceStatus.STARTING}
                />
            ))}
        </div>
    );
}

function ProgressBit(props: {
    label: string;
    units: string;
    value: number;
    isLoading?: boolean;
    disabled?: boolean;
}): JSX.Element {
    const isDisabled = props.disabled || props.isLoading || props.value === -1;

    return (
        <div className={[
            "progress-bit-container",
            props.label as ProgressBitTypes === ProgressBitTypes.DataLoading ? "progress-bar-version" : undefined,
            isDisabled ? "disabled" : undefined,
        ].filter(Boolean).join(" ")}>
            {!props.isLoading ? null :
                <div className="progress-overlay">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            }
            <div className="bit-label">{props.label}</div>
            {props.label as ProgressBitTypes === ProgressBitTypes.DataLoading ? 
                <div className="progress-bar-container">
                    <div className="progress-bar-content">
                        <div className="bit-value">{isDisabled ? "--" : props.value}%</div>
                        <div className="bit-units">{props.units}</div>
                    </div>
                    <div className="progress-bar">
                        <div className="fill-bar" style={{width: `${isDisabled ? "0" : props.value}%`}} />
                    </div>
                </div>
            :
                <div className="bit-content">
                    <div className="bit-value">{isDisabled ? "--" : props.value}</div>
                    <div className="bit-units">{props.units}</div>
                </div>
            }
        </div>
    );
}