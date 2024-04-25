import dayjs from "dayjs";
import { isInitializerDto } from "./actions/applicationDiscriminators";
import { S3DataRetrievalAppPipelineStructure } from "./dataRetrievalApps";
import type { AppInstanceObject, ApplicationType, ChartDataObject, FilterGroupStructure, FiltersStructure, Initializers, ModelDatasetObject, ModelObject, PipelineObject, PipelineStep, PipelineStepAddedInfo } from "./interfaces";
import { StepDataSource, StepDataType } from "./interfaces";
import { S3PreprocessingAppPipelineStructure } from "./preprocessingApps";




// EXPORTED FUNCTIONS


export function areShallowObjectsEqual(object1: Initializers | Record<string, unknown>, object2: Initializers | Record<string, unknown>, ignoreField?: string | string[]): boolean {
    for (const [key, value] of Object.entries(object1)) {
        if ((typeof ignoreField === "string" && key === ignoreField) ||
            (Array.isArray(ignoreField) && ignoreField.includes(key))) continue;
        else if (!object2[key] || object2[key] !== value) return false;
    }
    return true;
}


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


export function getUniqueTagsFromList(list: ModelObject[]|ModelDatasetObject[]): string[] {
    const tagsSet = new Set<string>();
    list.flatMap((listItem: { tags: string[]|null; }) => listItem.tags ?? []).forEach(tag => tagsSet.add(tag));
    return Array.from(tagsSet).sort();
}

export function getUniqueActiveFiltersFromGroup (filtering: FiltersStructure, groupName?: string): string[] {
    const activeTags = new Set<string>();  
    filtering.filters.forEach(filter => {
        if ('filters' in filter && (!groupName || filter.label === groupName)) {
            filter.filters.forEach(item => {
                if (item.isActive) {
                    activeTags.add(item.label);
                }
            });
        }
    });  
    return Array.from(activeTags);
};

export function countActiveFilters(filtering: FiltersStructure): number {
    let activeCount = 0;  
    function countActiveInGroup (group: FilterGroupStructure): number {
        return group.filters.reduce((count, filter) => {
            return count + (filter.isActive ? 1 : 0);
        }, 0);
    };  
    filtering.filters.forEach(filter => {
        if ('filters' in filter) {  // If it's a group
            activeCount += countActiveInGroup(filter);
        } else {
            activeCount += filter.isActive ? 1 : 0;
        }
    });  
    return activeCount;
};


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


export function getPearsonCorrelation(x: number[], y: number[]): number {
    if (x.length !== y.length) { return NaN; }
    const n = x.length;  
    // Calculate means
    const meanX = x.reduce((sum, val) => sum + val, 0) / n;
    const meanY = y.reduce((sum, val) => sum + val, 0) / n;  
    // Calculate the numerators and denominators for the correlation coefficient
    let numerator = 0;
    let denominatorX = 0;
    let denominatorY = 0;  
    for (let i = 0; i < n; i++) {
      const diffX = x[i] - meanX;
      const diffY = y[i] - meanY;  
      numerator += diffX * diffY;
      denominatorX += diffX ** 2;
      denominatorY += diffY ** 2;
    }  
    const denominator = Math.sqrt(denominatorX) * Math.sqrt(denominatorY);  
    if (denominator === 0) {
        return NaN;
    }  
    return numerator / denominator;
  }



// LOCAL FUNCTIONS




function getStepStructure(appId: string): PipelineStep[][] | undefined {
    switch (appId) {
      case "1": return S3DataRetrievalAppPipelineStructure;
      case "2": return S3PreprocessingAppPipelineStructure;
      default: return undefined;
    }
}
  