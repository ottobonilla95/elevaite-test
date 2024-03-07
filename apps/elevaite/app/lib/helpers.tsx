import { S3DataRetrievalAppPipelineStructure } from "./dataRetrievalApps";
import { isInitializerDto } from "./discriminators";
import type { Initializers, PipelineObject, PipelineStep } from "./interfaces";
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


export function getConfigurationObjectFromRaw(raw?: string): Initializers|undefined {
    if (!raw) return;
    const parsedConfiguration = JSON.parse(raw) as unknown;
    if (!isInitializerDto(parsedConfiguration)) return;
    return parsedConfiguration;
}






// LOCAL FUNCTIONS




function getStepStructure(appId: string): PipelineStep[][] | undefined {
    switch (appId) {
      case "1": return S3DataRetrievalAppPipelineStructure;
      case "2": return S3PreprocessingAppPipelineStructure;
      default: return undefined;
    }
}
  