"use client";
import { AppInstanceObject, ApplicationType } from "../../../lib/interfaces";
import "./WidgetDocker.scss";
import { ConsoleLogWidget } from "./widgets/ConsoleLogWidget";
import MainDetailsWidget from "./widgets/MainDetailsWidget";
import { PreprocessPipelineWidget } from "./widgets/PreprocessPipelineWidget";


interface WidgetDockerProps {
    applicationType?: ApplicationType;
    selectedInstance: AppInstanceObject | undefined;
    selectedFlow?: string;
}

export default function WidgetDocker(props: WidgetDockerProps): JSX.Element {



    return (
        <div className="widget-docker-container">
            <MainDetailsWidget instance={props.selectedInstance} />
            {!props.selectedInstance || !props.applicationType || props.applicationType != ApplicationType.PREPROCESS ? null :
                <PreprocessPipelineWidget selectedFlow={props.selectedFlow} />
            }
            <ConsoleLogWidget />
        </div>
    );
}