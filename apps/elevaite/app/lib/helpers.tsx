import dayjs from "dayjs";
import { isInitializerDto } from "./actions/applicationDiscriminators";
import { S3DataRetrievalAppPipelineStructure } from "./dataRetrievalApps";
import type { AppInstanceObject, ApplicationType, ChartDataObject, FilterGroupStructure, FiltersStructure, Initializers, ModelDatasetObject, ModelObject, PipelineObject, PipelineStep, PipelineStepAddedInfo } from "./interfaces";
import { StepDataSource, StepDataType } from "./interfaces";
import { S3PreprocessingAppPipelineStructure } from "./preprocessingApps";
import { useCallback, useRef } from "react";




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
    if (!detail.field || !instance || !appType) return "—";

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
        if (detail.type === StepDataType.DURATION) {
            if (!detail.secondaryField) return "—";
            const end = source[detail.secondaryField] as string;
            const startDate = dayjs(result);
            const endDate = dayjs(end);
            if (startDate.isValid() && endDate.isValid()) {
                return getElapsedTime(result, end);
            }
        }
        return result ? result : "—";
    }

    return "—";
}


export function getIsPositiveIntegerOrZero(token: string|number): boolean {
    return /^\+?\d+$/.test(token.toString());
}


export function formatBytes(bytes: number, decimals = 0): string {
    if (!Number(bytes)) return "0 B"

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm)).toString()} ${sizes[i]}`;
}


export function getElapsedTime(start: string, end?: string): string {
    let duration = dayjs(end ?? undefined).diff(dayjs(start)) / 1000;
    const result: string[] = [];

    const days = Math.floor(duration / 86400);
    duration -= days * 86400;
    if (days > 0) {
        result.push(`${days.toString()}d`);
    }
    const hours = Math.floor(duration / 3600) % 24;
    duration -= hours * 3600;
    if (days > 0 || hours > 0) {
        result.push(`${hours.toString().padStart(2, '0')}h`);
    }
    const minutes = Math.floor(duration / 60) % 60;
    duration -= minutes * 60;
    if (days > 0 || hours > 0 || minutes > 0) {
        result.push(`${minutes.toString().padStart(2, '0')}m`);
    }
    const seconds = Math.floor(duration % 60);
    result.push(`${seconds.toString().padStart(2, '0')}s`);

    return result.filter(Boolean).join(" ");
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




export const useDebouncedCallback = <T extends (...args: unknown[]) => void>(
        callback: T,
        delay: number
    ): (...args: Parameters<T>) => void => {
    const callbackRef = useRef(callback);
    const timerRef = useRef<number | undefined>(undefined);
  
    callbackRef.current = callback;
  
    return useCallback(
        (...args: Parameters<T>) => {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
            }
    
            timerRef.current = window.setTimeout(() => {
                callbackRef.current(...args);
            }, delay);
        },
        [delay]
    );
};





// LOCAL FUNCTIONS




function getStepStructure(appId: string): PipelineStep[][] | undefined {
    switch (appId) {
      case "1": return S3DataRetrievalAppPipelineStructure;
      case "2": return S3PreprocessingAppPipelineStructure;
      default: return undefined;
    }
}
  