"use client";
import dayjs from "dayjs";
import { createContext, useContext, useEffect, useState } from "react";
import { deleteModel, deployModel, getAvailableModels, getAvailableModelsByName, getEvaluationLogsById, getModelById, getModelDatasets, getModelEndpoints, getModelEvaluations, getModelLogs, getModelParametersById, getModels, getModelsTasks, registerModel, requestModelEvaluation } from "../actions/modelActions";
import { countActiveFilters, getUniqueActiveFiltersFromGroup, getUniqueTagsFromList } from "../helpers";
import { ModelsStatus, type AvailableModelObject, type EvaluationObject, type FiltersStructure, type ModelDatasetObject, type ModelEndpointObject, type ModelEvaluationLogObject, type ModelObject, type ModelParametersObject, type ModelRegistrationLogObject } from "../interfaces";



const AVAILABLE_MODELS_LIMIT = 10;



// ENUMS

export enum specialHandlingModelFields {
    STATUS = "status",
    TAGS = "tags",
    DATE = "date",
    RAM_TO_RUN = "ramToRun",
    RAM_TO_TRAIN = "ramToTrain",
}

export enum FilterStructureLabels {
    TAGS = "Tags",
    TASKS = "Tasks",
}





// STATIC OBJECTS


const defaultLoadingList: LoadingListObject = {
    models: false,
    modelTasks: false,
    modelLogs: false,
    modelEvaluations: false,
    endpoints: false,
    datasets: false,
    availableModels: false,
    currentModelParameters: false,
    registerModel: false,
    evaluateModel: false,
    deleteModel: false,
    model: undefined,
    filtersStructure: undefined,
};



// INTERFACES

interface SortingObject {
    field?: keyof ModelObject;
    isDesc?: boolean;
}

interface LoadingListObject {
    models: boolean|undefined;
    modelTasks: boolean|undefined;
    modelLogs: boolean|undefined;
    modelEvaluations: boolean|undefined;
    endpoints: boolean|undefined;
    datasets: boolean|undefined;
    availableModels: boolean|undefined;
    currentModelParameters: boolean|undefined;
    registerModel: boolean|undefined;
    evaluateModel: boolean|undefined;
    deleteModel: boolean|undefined;
    model: string|number|undefined;
    filtersStructure: boolean|undefined;
}


// STRUCTURE 

export interface ModelsContextStructure {
    models: ModelObject[];
    modelTasks: string[];
    availableModels: AvailableModelObject[];
    modelsSorting: SortingObject;
    selectedModel: ModelObject|undefined;
    setSelectedModel: (model: ModelObject|undefined) => void;
    selectedModelParameters: ModelParametersObject|undefined,
    refreshSelectedModel: () => void;
    refreshModelById: (modelId: string|number) => Promise<void>;
    getModelLogs: (modelId: string|number) => Promise<ModelRegistrationLogObject[]>;
    getModelEvaluations: (modelId: string|number) => Promise<EvaluationObject[]>;
    getEvaluationLogs: (evaluationId: string|number) => Promise<ModelEvaluationLogObject[]>;
    sortModels: (field: string, specialHandling?: string) => void;
    getAvailableRemoteModels: (task: string) => void;
    getAvailableRemoteModelsByName: (name: string) => void;
    registerModel: (modelName: string, modelRepo: string, tags?: string[]) => Promise<void>;
    deployModel: (modelId: string|number) => Promise<void>;
    deleteModel: (modelId: string|number) => Promise<void>;
    modelDatasets: ModelDatasetObject[],
    evaluateModel: (modelId: string|number, datasetId: string) => Promise<EvaluationObject|undefined>;
    filtering: FiltersStructure;
    activeFiltersCount: number;
    toggleFilter: (filterName: string) => void,
    toggleFilterGroup: (group: string) => void,
    loading: LoadingListObject;
}


export const ModelsContext = createContext<ModelsContextStructure>({
    models: [],
    modelTasks: [],
    availableModels: [],
    modelsSorting: {field: undefined},
    selectedModel: undefined,
    setSelectedModel: () => {/**/},
    selectedModelParameters: undefined,
    refreshSelectedModel: () => {/**/},
    refreshModelById: async () => {/**/},
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    getModelLogs: async () => { return []; },
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    getModelEvaluations: async () => { return []; },
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    getEvaluationLogs: async () => { return []; },
    sortModels: () => {/**/},
    getAvailableRemoteModels: () => {/**/},
    getAvailableRemoteModelsByName: () => {/**/},
    registerModel: async () => {/**/},
    deployModel: async () => {/**/},
    deleteModel: async () => {/**/},
    modelDatasets: [],
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    evaluateModel: async () => { return undefined; },
    filtering: {filters:[]},
    activeFiltersCount: 0,
    toggleFilter: () => {/**/},
    toggleFilterGroup: () => {/**/},
    loading: defaultLoadingList,
});





// FUNCTIONS

function sortDisplayModels(models: ModelObject[], sorting: SortingObject, specialHandling?: specialHandlingModelFields): ModelObject[] {    
    const statusSortOrder = [ModelsStatus.REGISTERING, ModelsStatus.FAILED, ModelsStatus.DEPLOYED, ModelsStatus.ACTIVE];

    switch (specialHandling) {
        case specialHandlingModelFields.STATUS: 
            models.sort((a,b) => statusSortOrder.indexOf(a.status) - statusSortOrder.indexOf(b.status));
            break;
        case specialHandlingModelFields.DATE:
            models.sort((a,b) => dayjs(a.created).valueOf() - dayjs(b.created).valueOf());
            break;
        case specialHandlingModelFields.TAGS:
            models.sort((a,b) => (!a.tags || !b.tags || a.tags.length > 0 === b.tags.length > 0) ? 0 : a.tags.length > 0 ? -1 : 1);
            break;
        default:
            if (sorting.field) {
                models.sort((a,b) => {
                    if (sorting.field && typeof a[sorting.field] === "string" && typeof b[sorting.field] === "string" && !Array.isArray(a[sorting.field]) && !Array.isArray(b[sorting.field]))
                    return (a[sorting.field] as string).localeCompare(b[sorting.field] as string);
                    return 0;
                })
            } else {
                models.sort((a,b) => dayjs(a.created).valueOf() - dayjs(b.created).valueOf());
            }
    }

    if (sorting.isDesc) {
        models.reverse();
    }
    return models;
}









// PROVIDER

interface ModelsContextProviderProps {
    children: React.ReactNode;
}


export function ModelsContextProvider(props: ModelsContextProviderProps): JSX.Element {
    const [models, setModels] = useState<ModelObject[]>([]);
    const [displayModels, setDisplayModels] = useState<ModelObject[]>([]);
    const [selectedModel, setSelectedModel] = useState<ModelObject|undefined>();
    const [selectedModelParameters, setSelectedModelParameters] = useState<ModelParametersObject|undefined>();
    const [modelTasks, setModelTasks] = useState<string[]>([]);
    const [modelEndpoints, setModelEndpoints] = useState<ModelEndpointObject[]>([]);
    const [modelDatasets, setModelDatasets] = useState<ModelDatasetObject[]>([]);
    const [availableModels, setAvailableModels] = useState<AvailableModelObject[]>([]);
    const [sorting, setSorting] = useState<SortingObject>({field: undefined});
    const [filtering, setFiltering] = useState<FiltersStructure>({filters: []});
    const [activeFiltersCount, setActiveFiltersCount] = useState(0);
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);


    useEffect(() => {
        setLoading(current => {return {...current, filtersStructure: true}} );
        void fetchModels();
        void fetchModelTasks();
        void fetchModelEndpoints();
        void fetchDatasets();
    }, []);

    useEffect(() => {
        if (loading.models === false && loading.modelTasks === false && loading.filtersStructure) constructFilters(displayModels, modelTasks);
    }, [models, modelTasks, loading.datasets, loading.modelTasks]);

    useEffect(() => {
        setDisplayModels(formatDisplayModels());
    }, [models, modelEndpoints]);

    useEffect(() => {
        setActiveFiltersCount(countActiveFilters(filtering));
        filterModels();
    }, [filtering]);



    function formatDisplayModels(): ModelObject[] {
        const modelsClone = JSON.parse(JSON.stringify(models)) as ModelObject[];
        const adjustedModels = modelsClone.map(model => {
            const foundEndpoint = modelEndpoints.find(endpoint => endpoint.model_id === model.id);
            if (foundEndpoint) {
                return {...model, status: ModelsStatus.DEPLOYED, endpointUrl: foundEndpoint.url, endpointId: foundEndpoint.endpoint_id.toString()};
            }
            return model;
        });
        if (selectedModel?.id) {
            const updatingSelectedModel = adjustedModels.find(item => item.id === selectedModel.id);
            if (updatingSelectedModel) setSelectedModel(updatingSelectedModel);
        }
        return sortDisplayModels(adjustedModels, sorting);
    }


    function filterModels(): void {
        const allModels = formatDisplayModels();
        const filteredModels: ModelObject[] = [];

        // If there are no active filters, reset the list
        if (countActiveFilters(filtering) === 0) {
            setDisplayModels(allModels);
            return;
        }

        // Get all active tasks
        const activeTasks = getUniqueActiveFiltersFromGroup(filtering, FilterStructureLabels.TASKS);
        // // Get all active tags
        const activeTags = getUniqueActiveFiltersFromGroup(filtering, FilterStructureLabels.TAGS);

        // // For each item decide if to add it or not.
        for (const model of allModels) {
            let show = false;
            if (model.task && activeTasks.includes(model.task)) show = true;
            if (!show && model.tags?.some(item => activeTags.includes(item))) show = true;
            if (show) filteredModels.push(model);
        }
        setDisplayModels(filteredModels);
    }


    function sortModels(field: keyof ModelObject, specialHandling?: specialHandlingModelFields): void {
        let sortingResult: SortingObject = {};
        if (sorting.field !== field) sortingResult = {field};
        if (sorting.field === field) {
            if (sorting.isDesc) sortingResult = {field: undefined};
            else sortingResult = {field, isDesc: true};
        }
        setSorting(sortingResult);
        
        if (displayModels.length === 0) return;
        setDisplayModels(sortDisplayModels(displayModels, sortingResult, specialHandling));
    }


    function constructFilters(passedModels: ModelObject[], tasks: string[]): void {
        const constructedFilters: FiltersStructure = { label: "Filters", filters: []};
        // Tags
        const uniqueTags = getUniqueTagsFromList(passedModels);
        constructedFilters.filters.push({
            label: FilterStructureLabels.TAGS,
            filters: uniqueTags.map(tag => { return { label: tag }; })
        })
        // Tasks
        constructedFilters.filters.push({
            label: FilterStructureLabels.TASKS,
            filters: tasks.map(task => { return { label: task }; })
        })        
        setFiltering(constructedFilters);
        setLoading(current => {return {...current, filtersStructure: false}} );
    }
    function toggleFilterGroup(group: string): void {
        setFiltering(prevSorting => ({
            ...prevSorting,
            filters: prevSorting.filters.map(foundGroup => {
              if ("filters" in foundGroup && foundGroup.label === group) {
                return {
                  ...foundGroup,
                  isClosed: !foundGroup.isClosed
                };
              }
              return foundGroup;
            })
        }));
    }

    function toggleFilter(filterName: string): void {
        setFiltering(prevSorting => ({
            ...prevSorting,
            filters: prevSorting.filters.map(foundFilter => {
              if ('filters' in foundFilter) {  // Check if it's a group
                return {
                  ...foundFilter,
                  filters: foundFilter.filters.map(subFilter => {
                    if (subFilter.label === filterName) {
                      return {
                        ...subFilter,
                        isActive: !subFilter.isActive
                      };
                    }
                    return subFilter;
                  })
                };
              } else if (foundFilter.label === filterName) {  // If it's a single filter
                return {
                  ...foundFilter,
                  isActive: !foundFilter.isActive
                };
              }
              return foundFilter;
            })
        }));
    }


    function remoteSetSelectedModel(model: ModelObject|undefined): void {
        if (!model || selectedModel === model) {
            setSelectedModel(undefined);
            setSelectedModelParameters(undefined);
        } else {
            setSelectedModel(model);
            if (model.status === ModelsStatus.ACTIVE || model.status === ModelsStatus.DEPLOYED) {
                void fetchSelectedModelParameters(model.id);
            }
        }
    }

    async function refreshModelById(modelId: string|number): Promise<void> {
        if (loading.model === modelId) return;
        const fetchedModel = await fetchModelById(modelId);
        if (!fetchedModel) return;
        setModels(current =>
            current.map(model => model.id === fetchedModel.id ? fetchedModel : model)
        );
    }

    function refreshSelectedModel(): void {
        if (!selectedModel) return;
        if (selectedModel.status === ModelsStatus.ACTIVE || selectedModel.status === ModelsStatus.DEPLOYED) {
            void fetchSelectedModelParameters(selectedModel.id);
            // void fetchModelById(selectedModel.id); // This doesn't do anything different for the time being.
        }
    }

    function getAvailableRemoteModels(task: string): void {
        void fetchAvailableModels(task);
    }
    function getAvailableRemoteModelsByName(name: string): void {
        void fetchAvailableModelsByName(name);
    }

    async function fetchModels(): Promise<void> {
        try {
            setLoading(current => {return {...current, models: true}} );
            const fetchedModels = await getModels();
            setModels(fetchedModels);
            // console.log("Fetched models", fetchedModels);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching models:", error);
        } finally {                
            setLoading(current => {return {...current, models: false}} );
        }
    }

    async function fetchModelTasks(): Promise<void> {
        try {
            setLoading(current => {return {...current, modelTasks: true}} );
            const fetchedModelTasks = await getModelsTasks();
            fetchedModelTasks.sort();
            setModelTasks(fetchedModelTasks);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching model tasks:", error);
        } finally {                
            setLoading(current => {return {...current, modelTasks: false}} );
        }
    }

    async function fetchModelLogs(modelId: string|number): Promise<ModelRegistrationLogObject[]> {
        try {
            setLoading(current => {return {...current, modelLogs: true}} );
            const fetchedModelLogs = await getModelLogs(modelId);
            return fetchedModelLogs;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching model logs:", error);
            return [];
        } finally {                
            setLoading(current => {return {...current, modelLogs: false}} );
        }
    }

    async function fetchEvaluationLogs(evaluationId: string|number): Promise<ModelEvaluationLogObject[]> {
        try {
            setLoading(current => {return {...current, modelLogs: true}} );
            const fetchedEvaluationLogs = await getEvaluationLogsById(evaluationId);
            return fetchedEvaluationLogs;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching evaluation logs:", error);
            return [];
        } finally {                
            setLoading(current => {return {...current, modelLogs: false}} );
        }
    }

    async function fetchModelEvaluations(modelId: string|number): Promise<EvaluationObject[]> {
        try {
            setLoading(current => {return {...current, modelLogs: true}} );
            const fetchedModelEvaluations = await getModelEvaluations(modelId);
            return fetchedModelEvaluations;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching model evaluations:", error);
            return [];
        } finally {                
            setLoading(current => {return {...current, modelLogs: false}} );
        }
    }

    async function fetchModelEndpoints(): Promise<void> {
        try {
            setLoading(current => {return {...current, endpoints: true}} );
            const fetchedEndpoints = await getModelEndpoints();
            setModelEndpoints(fetchedEndpoints);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching model endpoints:", error);
        } finally {                
            setLoading(current => {return {...current, endpoints: false}} );
        }
    }

    async function fetchDatasets(): Promise<void> {
        try {
            setLoading(current => {return {...current, datasets: true}} );
            const fetchedDatasets = await getModelDatasets();
            setModelDatasets(fetchedDatasets);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching datasets:", error);
        } finally {
            setLoading(current => {return {...current, datasets: false}} );
        }
    }

    async function fetchAvailableModels(task: string): Promise<void> {
        try {
            setLoading(current => {return {...current, availableModels: true}} );
            const result = await getAvailableModels(task, AVAILABLE_MODELS_LIMIT);
            setAvailableModels(result);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching available models:", error);
        } finally {                
            setLoading(current => {return {...current, availableModels: false}} );
        }
    }

    async function fetchAvailableModelsByName(name: string): Promise<void> {
        try {
            setLoading(current => {return {...current, availableModels: true}} );
            const result = await getAvailableModelsByName(name, AVAILABLE_MODELS_LIMIT);
            setAvailableModels(result);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching available models:", error);
        } finally {                
            setLoading(current => {return {...current, availableModels: false}} );
        }
    }

    async function fetchModelById(modelId: string|number): Promise<ModelObject|undefined> {
        try {
            setLoading(current => {return {...current, model: modelId}} );
            const result = await getModelById(modelId);
            return result;
        } catch(error) {            
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching model:", error);
        } finally {                
            setLoading(current => {return {...current, model: undefined}} );
        }
    }

    async function fetchSelectedModelParameters(modelId: string|number): Promise<void> {
        try {
            setLoading(current => {return {...current, currentModelParameters: true}} );
            const result = await getModelParametersById(modelId);
            setSelectedModelParameters(result);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {
            setLoading(current => {return {...current, currentModelParameters: false}} );
        }
    }


    async function actionRegisterModel(modelName: string, modelRepo: string, tags?: string[]): Promise<void> {
        try {
            setLoading(current => {return {...current, registerModel: true}} );
            const registeredModel = await registerModel(modelName, modelRepo, tags);
            setModels(current => [...current, registeredModel]);
            if (selectedModel?.id === registeredModel.id) setSelectedModel(registeredModel);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {
            setLoading(current => {return {...current, registerModel: false}} );
        }
    }


    async function actionDeployModel(modelId: string|number): Promise<void> {
        try {
            setLoading(current => {return {...current, registerModel: true}} );
            await deployModel(modelId);
            await fetchModelEndpoints();
            if (selectedModel?.id === modelId) await refreshModelById(modelId);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {
            setLoading(current => {return {...current, registerModel: false}} );
        }
    }



    async function actionEvaluateModel(modelId: string|number, datasetId: string): Promise<EvaluationObject|undefined> {
        try {
            setLoading(current => {return {...current, evaluateModel: true}} );
            const requestResponse = await requestModelEvaluation(modelId, datasetId);
            return requestResponse;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {
            setLoading(current => {return {...current, evaluateModel: false}} );
        }
    }

    async function actionDeleteModel(modelId: string|number): Promise<void> {
        try {
            setLoading(current => {return {...current, deleteModel: true}} );
            const result = await deleteModel(modelId.toString());
            if (result) {
                setModels(current => current.filter(item => item.id.toString() !== modelId));                
                if (selectedModel?.id === modelId) setSelectedModel(undefined);
            }
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {
            setLoading(current => {return {...current, deleteModel: false}} );
        }
    }


  
    return (
        <ModelsContext.Provider
            value={ {
                models: displayModels,
                modelTasks,
                availableModels,
                modelsSorting: sorting,
                selectedModel,
                setSelectedModel: remoteSetSelectedModel,
                selectedModelParameters,
                refreshSelectedModel,
                refreshModelById,
                sortModels,
                getModelLogs: fetchModelLogs,
                getModelEvaluations: fetchModelEvaluations,
                getEvaluationLogs: fetchEvaluationLogs,
                getAvailableRemoteModels,
                getAvailableRemoteModelsByName,
                registerModel: actionRegisterModel,
                deployModel: actionDeployModel,
                deleteModel: actionDeleteModel,
                modelDatasets,
                evaluateModel: actionEvaluateModel,
                filtering,
                activeFiltersCount,
                toggleFilter,
                toggleFilterGroup,
                loading,
            } }
        >
            {props.children}
        </ModelsContext.Provider>
    );
}
  
export function useModels(): ModelsContextStructure {
    return useContext(ModelsContext);
}