"use client";
import { ReactNode, useEffect, useState } from "react";
import { AppInstanceObject, ApplicationType } from "../../../lib/interfaces";
import "./WidgetDocker.scss";
import { ConsoleLogWidget } from "./widgets/ConsoleLogWidget";
import MainDetailsWidget from "./widgets/MainDetailsWidget";
import { PreprocessPipelineWidget } from "./widgets/PreprocessPipelineWidget";
import { ProgressTrackingWidget } from "./widgets/ProgressTrackingWidget";


interface WidgetDockerProps {
    applicationId: string | null;
    applicationType?: ApplicationType;
    selectedInstance: AppInstanceObject | undefined;
    selectedFlow?: string;
}

export default function WidgetDocker(props: WidgetDockerProps): JSX.Element {
    const [displayedWidgets, setDIsplayedWidgets] = useState<ReactNode>();


    useEffect(() => {
        setDIsplayedWidgets(getConditionalWidgets());
    }, [props.selectedInstance]);


    function getConditionalWidgets(): ReactNode {
        if (!props.selectedInstance || !props.applicationType) return null;
        switch (props.applicationType) {
            case ApplicationType.INGEST: return props.selectedInstance ? <ProgressTrackingWidget applicationId={props.applicationId} instance={props.selectedInstance} /> : null;
            case ApplicationType.PREPROCESS: return <PreprocessPipelineWidget selectedFlow={props.selectedFlow} />
        }
    }

    return (
        <div className="widget-docker-container">
            <div className="widget-docker-contents">
                <MainDetailsWidget instance={props.selectedInstance} />
                {displayedWidgets}
                <ConsoleLogWidget instance={props.selectedInstance} />
            </div>
        </div>
    );
}