"use client";
import { ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { getInstanceChartData } from "../../../../lib/actions";
import type { AppInstanceObject, ChartDataObject } from "../../../../lib/interfaces";
import { AppInstanceStatus } from "../../../../lib/interfaces";
import "./ProgressTrackingWidget.scss";

enum ProgressBitTypes {
    docsIngested = "Docs Ingested",
    averageDocSize = "Avg Doc Size",
    totalPages = "Total Pages",
    totalChukns = "Total Chunks",
    dataLoading = "Data Loading Progress",
}

const progressBits = [
    { label: ProgressBitTypes.docsIngested, units: "files", value: -1 },
    { label: ProgressBitTypes.averageDocSize, units: "KB", value: -1 },
    // {   label: ProgressBitTypes.totalPages,
    //     units: "pp.",
    //     value: -1,     },
    // {   label: ProgressBitTypes.totalChukns,
    //     units: "chunks",
    //     value: -1,     },
    { label: ProgressBitTypes.dataLoading, units: "Completion", value: -1 },
];

interface ProgressTrackingWidgetProps {
    applicationId: string | null;
    instance: AppInstanceObject;
}

export function ProgressTrackingWidget(props: ProgressTrackingWidgetProps): JSX.Element {
    const [chartData, setChartData] = useState<ChartDataObject>();
    const [displayBits, setDisplayBits] = useState(progressBits);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        setIsLoading(true);
    }, [props.applicationId, props.instance]);

    useEffect(() => {
        //TODO: @Thanos please check
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TODO: Check
        if (!props.instance) return;
        if (props.instance.chartData) setChartData(props.instance.chartData);
        if (props.instance.status === AppInstanceStatus.RUNNING) {
            void fetchChartData();
            const interval = setInterval(() => {
                void fetchChartData();
            }, 5000);
            return () => {
                clearInterval(interval);
            };
        }
        setIsLoading(false);
    }, [props.instance]);

    useEffect(() => {
        if (!chartData) return;
        const modifiedBits = structuredClone(displayBits);

        // docs ingested
        const docsIngested = modifiedBits.find((item) => item.label === ProgressBitTypes.docsIngested);
        //TODO: @Thanos please check
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TODO: Check
        if (docsIngested) docsIngested.value = chartData.ingestedItems ?? 0;
        // average doc size
        const avgSize = modifiedBits.find((item) => item.label === ProgressBitTypes.averageDocSize);
        if (avgSize)
            avgSize.value = Math.round(
                //TODO: @Thanos please check
                // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TODO: Check
                chartData && chartData.totalItems > 0 ? chartData.totalSize / chartData.totalItems / 1024 : 0
            );
        // progress
        const loadingProgress = modifiedBits.find((item) => item.label === ProgressBitTypes.dataLoading);
        if (loadingProgress)
            loadingProgress.value = Math.round(
                //TODO: @Thanos please check
                // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TODO: Check
                chartData && chartData.totalSize > 0 ? (chartData.ingestedSize / chartData.totalSize) * 100 : 0
            );

        setDisplayBits(modifiedBits);
    }, [chartData]);

    async function fetchChartData() {
        //TODO: @Thanos please check
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TODO: Check
        if (!props.applicationId || !props.instance) return;
        try {
            const fetchedData = await getInstanceChartData(props.applicationId, props.instance.id);
            //TODO: @Thanos please check
            // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TODO: Check
            if (fetchedData) setChartData(fetchedData);
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
                    disabled={props.instance.status === AppInstanceStatus.STARTING}
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
        <div
            className={[
                "progress-bit-container",
                //TODO: @Thanos please check
                // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison -- TODO: Check
                props.label === ProgressBitTypes.dataLoading ? "loading-bar-version" : undefined,
                isDisabled ? "disabled" : undefined,
            ]
                .filter(Boolean)
                .join(" ")}
        >
            {!props.isLoading ? null : (
                <div className="loading-overlay">
                    <ElevaiteIcons.SVGSpinner />
                </div>
            )}
            <div className="bit-label">{props.label}</div>
            {
                //TODO: @Thanos please check
                // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison -- TODO: Check
                props.label === ProgressBitTypes.dataLoading ? (
                    <div className="loading-bar-container">
                        <div className="loading-bar-content">
                            <div className="bit-value">{isDisabled ? "--" : props.value}%</div>
                            <div className="bit-units">{props.units}</div>
                        </div>
                        <div className="loading-bar">
                            <div className="fill-bar" style={{ width: `${isDisabled ? "0" : props.value}%` }} />
                        </div>
                    </div>
                ) : (
                    <div className="bit-content">
                        <div className="bit-value">{isDisabled ? "--" : props.value}</div>
                        <div className="bit-units">{props.units}</div>
                    </div>
                )
            }
        </div>
    );
}
