import dayjs from "dayjs";
import { S3DataRetrievalAppPipelineStructure } from "./dataRetrievalApps";
import { isInitializerDto } from "./discriminators";
import type { AppInstanceObject, ApplicationType, ChartDataObject, Initializers, PipelineObject, PipelineStep, PipelineStepAddedInfo } from "./interfaces";
import { StepDataSource, StepDataType } from "./interfaces";
import { S3PreprocessingAppPipelineStructure } from "./preprocessingApps";




// EXPORTED FUNCTIONS


export function attachSideInfoToPipelineSteps(pipelines: PipelineObject[], appId: string|null): PipelineObject[] {
    if (appId === null) return pipelines;
    const structure = getStepStructure(appId);
    if (!structure) return pipelines;
    const flatStructure = structure.flat();
    const formattedPipelines = JSON.parse(JSON.stringify(pipelines)) as PipelineObject[];    

    for (const pipeline of formattedPipelines) {
        if (pipeline.steps.length > 0) {
            for (const step of pipeline.steps) {
                const match = flatStructure.find(item => item.title === step.title);
                if (match) {
                    step.addedInfo = match.addedInfo;
                    step.sideDetails = match.sideDetails;
                }
            }
        }
    }
    return formattedPipelines;
}


export function getConfigurationObjectFromRaw(raw?: unknown): Initializers|undefined {
    if (!raw) return;
    const parsedConfiguration = typeof raw === "string" ? JSON.parse(raw) as unknown : raw;
    if (!isInitializerDto(parsedConfiguration)) return;
    return parsedConfiguration;
}



export function getDisplayValueFromStepDetail(detail: PipelineStepAddedInfo, step?: PipelineStep, instance?: AppInstanceObject, appType?: ApplicationType): string {
    if (!detail.field || !instance || !appType) return "";

    let source: PipelineStep | Initializers | AppInstanceObject | ChartDataObject | undefined;
    switch (detail.source) {
        case StepDataSource.CONFIG: source = getConfigurationObjectFromRaw(instance.configuration?.raw); break;
        case StepDataSource.INSTANCE: source = instance; break;
        case StepDataSource.CHART: source = instance.chartData; break;
        case StepDataSource.STEP: source = step; break;
        default: source = instance; break;
    }

    if (source?.[detail.field] && (typeof source[detail.field] === "string" || typeof source[detail.field] === "number")) {
        const result = source[detail.field] as string;
        if (detail.type === StepDataType.DATE) return dayjs(result).format("DD-MMM-YYYY, hh:mm:ss a");
        return result;
    }

    return "";
}






// LOCAL FUNCTIONS




function getStepStructure(appId: string): PipelineStep[][] | undefined {
    switch (appId) {
      case "1": return S3DataRetrievalAppPipelineStructure;
      case "2": return S3PreprocessingAppPipelineStructure;
      default: return undefined;
    }
}
  