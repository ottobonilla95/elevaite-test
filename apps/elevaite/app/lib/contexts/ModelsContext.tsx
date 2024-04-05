"use client";
import dayjs from "dayjs";
import { createContext, useContext, useEffect, useState } from "react";
import { deleteModel, getAvailableModels, getModelDatasets, getModelById, getModelParametersById, getModels, getModelsTasks, registerModel, getAvailableModelsByName } from "../actions/modelActions";
import type { AvailableModelObject, EvaluationObject, ModelDatasetObject, ModelObject, ModelParametersObject } from "../interfaces";
import { ModelsStatus } from "../interfaces";



const AVAILABLE_MODELS_LIMIT = 10;



// ENUMS

export enum specialHandlingModelFields {
    STATUS = "status",
    TAGS = "tags",
    DATE = "date",
}




// STATIC OBJECTS


const defaultLoadingList: LoadingListObject = {
    models: false,
    modelTasks: false,
    datasets: false,
    availableModels: false,
    currentModelParameters: false,
    registerModel: false,
    deleteModel: false,
    model: undefined,
};



// INTERFACES

interface SortingObject {
    field?: keyof ModelObject;
    isDesc?: boolean;
}

interface LoadingListObject {
    models: boolean;
    modelTasks: boolean;
    datasets: boolean;
    availableModels: boolean;
    currentModelParameters: boolean;
    registerModel: boolean;
    deleteModel: boolean;
    model: string|number|undefined;
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
    sortModels: (field: string, specialHandling?: string) => void;
    getAvailableRemoteModels: (task: string) => void;
    getAvailableRemoteModelsByName: (task: string) => void;
    registerModel: (modelName: string, modelRepo: string, tags?: string[]) => Promise<void>;
    deleteModel: (modelId: string|number) => Promise<void>;
    evaluations: EvaluationObject[],
    evaluateModel: (modelId: string|number, dataset: ModelDatasetObject) => void;
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
    sortModels: () => {/**/},
    getAvailableRemoteModels: () => {/**/},
    getAvailableRemoteModelsByName: () => {/**/},
    registerModel: async () => {/**/},
    deleteModel: async () => {/**/},
    evaluations: [],
    evaluateModel: () => {/**/},
    loading: defaultLoadingList,
});





// FUNCTIONS

function sortDisplayModels(models: ModelObject[], sorting: SortingObject, specialHandling?: specialHandlingModelFields): ModelObject[] {    
    const statusSortOrder = [ModelsStatus.REGISTERING, ModelsStatus.FAILED, ModelsStatus.DEPLOYED, ModelsStatus.ACTIVE];

    switch (specialHandling) {
        case specialHandlingModelFields.STATUS: 
            models.sort((a,b) => !a.status || !b.status ? 0 : statusSortOrder.indexOf(a.status) - statusSortOrder.indexOf(b.status));
            break;
        case specialHandlingModelFields.DATE:
            models.sort((a,b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf());
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
                models.sort((a,b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf());
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
    const [selectedModel, setSelectedModel] = useState<ModelObject|undefined>();
    const [selectedModelParameters, setSelectedModelParameters] = useState<ModelParametersObject|undefined>();
    const [modelTasks, setModelTasks] = useState<string[]>([]);
    const [datasets, setDatasets] = useState<ModelDatasetObject[]>([]);
    const [availableModels, setAvailableModels] = useState<AvailableModelObject[]>([]);
    const [displayModels, setDisplayModels] = useState<ModelObject[]>([]);
    const [sorting, setSorting] = useState<SortingObject>({field: undefined});
    const [evaluations, setEvaluations] = useState<EvaluationObject[]>([]);
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);


    useEffect(() => {
        void fetchModels();
        void fetchModelTasks();
        void fetchDatasets();
    }, []);

    useEffect(() => {
        console.log("models", models);
        const modelsClone = JSON.parse(JSON.stringify(models)) as ModelObject[];
        setDisplayModels(sortDisplayModels(modelsClone, sorting));
    }, [models]);



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
        console.log("Refreshed model", fetchedModel);
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

    async function fetchDatasets(): Promise<void> {
        try {
            setLoading(current => {return {...current, datasets: true}} );
            const fetchedDatasets = await getModelDatasets();
            setDatasets(fetchedDatasets);
            // console.log("Fetched datasets", fetchedDatasets);
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
            const result = await registerModel(modelName, modelRepo, tags);
            setModels(current => [...current, result]);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {
            setLoading(current => {return {...current, registerModel: false}} );
        }
    }

    function evaluateModel(modelId: string|number, dataset: ModelDatasetObject): void {
        const evaluation: EvaluationObject = {
            modelId,
            datasetName: dataset.name,
            name: `Model Evaluation #${(evaluations.length+1).toString()}`,
            processor: "CPU",
            latency: `${Math.floor(Math.random() * 300).toString()} ms`,
            costPerToken: `${Math.floor(Math.random() * 3).toString()}.${Math.floor(Math.random() * 9).toString()} ¢`,
        }
        setEvaluations(current => [evaluation, ...current]);
    }

    async function actionDeleteModel(modelId: string|number): Promise<void> {
        try {
            setLoading(current => {return {...current, deleteModel: true}} );
            const result = await deleteModel(modelId.toString());
            if (result) {
                setModels(current => current.filter(item => item.id.toString() !== modelId));
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
                getAvailableRemoteModels,
                getAvailableRemoteModelsByName,
                registerModel: actionRegisterModel,
                deleteModel: actionDeleteModel,
                evaluations,
                evaluateModel,
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