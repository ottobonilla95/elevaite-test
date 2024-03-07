"use client";
import { useEffect, useState } from "react";
import { getInstanceChartData } from "../../../../lib/actions";
import { getConfigurationObjectFromRaw } from "../../../../lib/helpers";
import type { AppInstanceObject, ChartDataObject, Initializers, S3IngestFormDTO, S3PreprocessFormDTO } from "../../../../lib/interfaces";
import { AppInstanceStatus, ApplicationType } from "../../../../lib/interfaces";
import "./ProgressTrackingWidget.scss";


enum ProgressBitTypes {
    AverageFileSize = "Avg File Size",
    TotalFiles = "Total Files",
    TotalSize = "Total Size",
}

const progressBits = [
    {   label: ProgressBitTypes.TotalSize,
        units: "KB",
        value: -1,     },
    {   label: ProgressBitTypes.AverageFileSize,
        units: "KB",
        value: -1,     },
    {   label: ProgressBitTypes.TotalFiles,
        units: "files",
        value: -1,     },
];



interface ProgressTrackingWidgetProps {
    applicationId: string | null;
    type?: ApplicationType;
    instance?: AppInstanceObject;
}

export function ProgressTrackingWidget(props: ProgressTrackingWidgetProps): JSX.Element {
    const [chartData, setChartData] = useState<ChartDataObject>();
    const [displayBits, setDisplayBits] = useState(progressBits);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedInstanceConfiguration, setSelectedInstanceConfiguration] = useState<Initializers|undefined>();


    useEffect(() => {
        setIsLoading(true);
        setSelectedInstanceConfiguration(getConfigurationObjectFromRaw(props.instance?.configuration?.raw));
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

        // total size
        const totalSize = modifiedBits.find(item => item.label === ProgressBitTypes.TotalSize);
        if (totalSize) totalSize.value = Math.round(chartData.totalSize > 0 ? (chartData.totalSize / 1024) : 0);
        // average file size
        const avgSize = modifiedBits.find(item => item.label === ProgressBitTypes.AverageFileSize);
        if (avgSize) avgSize.value = Math.round(chartData.totalItems > 0 ? (chartData.totalSize / chartData.totalItems / 1024) : 0);
        // total files
        const totalFiles = modifiedBits.find(item => item.label === ProgressBitTypes.TotalFiles);
        if (totalFiles) totalFiles.value = chartData.totalItems;

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
            <ProgressBitInfo
                type={props.type}
                configuration={selectedInstanceConfiguration}
                isSkeleton={!props.instance}
            />
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




function ProgressBitInfo(props: {
    configuration?: Initializers;
    type?: ApplicationType;
    isSkeleton?: boolean;
}): JSX.Element {
    const [details, setDetails] = useState(
        {
            mainLabel: "",
            mainValue: "",
            secondaryLabel: "",
            secondaryValue: "",
            lastProgress: ""
        });


    useEffect(() => {
        if (props.type === ApplicationType.INGEST) {
            const conf: S3IngestFormDTO | undefined = props.configuration ? props.configuration as S3IngestFormDTO : undefined;
            setDetails({
                mainLabel: "Dataset Name:",
                mainValue: conf ? conf.name : "",
                secondaryLabel: "S3 URI:",
                secondaryValue: conf ? conf.url : "",
                lastProgress: "New Instance",
            });
        } else if (props.type === ApplicationType.PREPROCESS) {            
            const conf: S3PreprocessFormDTO | undefined = props.configuration ? props.configuration as S3PreprocessFormDTO : undefined;
            setDetails({
                mainLabel: "Pipeline Name:",
                mainValue: conf ? conf.name : "",
                secondaryLabel: "Input Dataset:",
                secondaryValue: conf ? conf.datasetName : "",
                lastProgress: "New Instance",
            });
        }
    }, [props.type, props.configuration]);


    return (
        <div className="progress-bit-info-container">
            <div className="info-row">
                <span className="label">{details.mainLabel}</span>
                {props.isSkeleton ? <div className="skeleton small"/> :
                    <div className="text" title={details.mainValue}>{details.mainValue}</div>
                }
            </div>
            <div className="info-row">
                <span className="label">{details.secondaryLabel}</span>
                {props.isSkeleton ? <div className="skeleton large"/> :
                    <div className="text" title={details.secondaryValue}>{details.secondaryValue}</div>
                }
            </div>
            <div className={["info-row", props.isSkeleton ? undefined : "extra"].filter(Boolean).join(" ")}>
                {props.isSkeleton ? <><div/><div className="skeleton dark"/></> :
                    <span className="text">
                        <span>{props.type ? `Last ${props.type}: ` : "Last progress: "}</span>
                        {details.lastProgress}
                    </span>
                }
            </div>
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
            isDisabled ? "disabled" : undefined,
        ].filter(Boolean).join(" ")}>
            {/* {!props.isLoading ? null :
                <div className="progress-overlay">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            } */}
            <div className="bit-label">{props.label}</div>
            <div className="bit-content">
                <div className="bit-value">{isDisabled ? "--" : props.value}</div>
                <div className="bit-units">{props.units}</div>
            </div>
        </div>
    );
}