"use client";
import { createContext, useContext, useEffect, useState } from "react";
import dayjs from "dayjs";
import type { AvailableModelObject, ModelObject, ModelParametersObject} from "../interfaces";
import { ModelsStatus } from "../interfaces";
import { getAvailableModels, getModelById, getModelParametersById, getModels, getModelsTasks } from "../actions";



const AVAILABLE_MODELS_LIMIT = 10;



// ENUMS

export enum specialHandlingModelFields {
    STATUS = "status",
    TAGS = "tags",
    DATE = "date",
}




// STATIC OBJECTS

const TEST: ModelObject[] = [
    {
        id: "Test_1",
        created_at: dayjs().toISOString(),
        task: "question-answering",
        name: "Test model 1",
        status: ModelsStatus.ACTIVE,
        tags: ["Test Tag 1", "Test Tag 2"],
        ramToRun: "24 GB",
        ramToTrain: "80 GB",
    },
    {
        id: "Test_2",
        created_at: dayjs().subtract(1, "hour").toISOString(),
        task: "question-answering",
        name: "Test model 2",
        status: ModelsStatus.REGISTERING,
        tags: ["Test Tag 1", "Test Tag 2", "Test Tag 3", "Test Tag 4"],
        ramToRun: "24 GB",
        ramToTrain: "64 GB",
    },
    {
        id: "Test_3",
        created_at: dayjs().subtract(15, "minutes").toISOString(),
        task: "token-classification",
        name: "Test model 3",
        status: ModelsStatus.FAILED,
        tags: [],
        ramToRun: "16 GB",
        ramToTrain: "24 GB",
    },
    {
        id: "Test_4",
        created_at: dayjs().subtract(1, "minute").toISOString(),
        task: "token-classification",
        name: "Test model 4",
        status: ModelsStatus.DEPLOYED,
        endpointUrl: "testURL",
        tags: ["Test Tag 1"],
        ramToRun: "24 GB",
        ramToTrain: "64 GB",
    },
];


const defaultLoadingList: LoadingListObject = {
    models: false,
    modelTasks: false,
    availableModels: false,
    currentModelParameters: false,
};



// INTERFACES

interface SortingObject {
    field?: keyof ModelObject;
    isDesc?: boolean;
}

interface LoadingListObject {
    models?: boolean;
    modelTasks?: boolean;
    availableModels?: boolean;
    currentModelParameters?: boolean;
}


// STRUCTURE 

export interface ModelsContextStructure {
    models: ModelObject[];
    modelTasks: string[];
    availableModels: AvailableModelObject[];
    modelsSorting: SortingObject;
    selectedModel: ModelObject|undefined;
    setSelectedModel: (model: ModelObject|undefined) => void;
    refreshSelectedModel: () => void;
    sortModels: (field: string, specialHandling?: string) => void;
    getAvailableRemoteModels: (task: string) => void;
    loading: LoadingListObject;
}


export const ModelsContext = createContext<ModelsContextStructure>({
    models: [],
    modelTasks: [],
    availableModels: [],
    modelsSorting: {field: undefined},
    selectedModel: undefined,
    setSelectedModel: () => {/**/},
    refreshSelectedModel: () => {/**/},
    sortModels: () => {/**/},
    getAvailableRemoteModels: () => {/**/},
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


// FETCHING

async function fetchModelTasks(): Promise<string[]> {
    const result = await getModelsTasks();
    result.sort();
    return result;
}








// PROVIDER

interface ModelsContextProviderProps {
    children: React.ReactNode;
}


export function ModelsContextProvider(props: ModelsContextProviderProps): JSX.Element {
    const [models, setModels] = useState<ModelObject[]>(TEST);
    const [selectedModel, setSelectedModel] = useState<ModelObject|undefined>();
    const [selectedModelParameters, setSelectedModelParameters] = useState<ModelParametersObject>();
    const [modelTasks, setModelTasks] = useState<string[]>([]);
    const [availableModels, setAvailableModels] = useState<AvailableModelObject[]>([]);
    const [displayModels, setDisplayModels] = useState<ModelObject[]>([]);
    const [sorting, setSorting] = useState<SortingObject>({field: undefined});
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);


    useEffect(() => {
        void (async () => {
            try {
                setLoading(current => {return {...current, models: true}} )
                const fetchedModels = await getModels();
                setModels(fetchedModels);
                console.log("Fetched models", fetchedModels);
            } catch(error) {
                // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
                console.error("Error in fetching models:", error);
            } finally {                
                setLoading(current => {return {...current, models: false}} )
            }
        })();
        void (async () => {            
            try {
                setLoading(current => {return {...current, modelTasks: true}} )
                const fetchedModelTasks = await fetchModelTasks();
                setModelTasks(fetchedModelTasks);
            } catch(error) {
                // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
                console.error("Error in fetching model tasks:", error);
            } finally {                
                setLoading(current => {return {...current, modelTasks: false}} )
            }
        })();
    }, []);

    useEffect(() => {
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
            void fetchSelectedModelParameters(model.id);
        }
    }

    function refreshSelectedModel(): void {
        if (!selectedModel) return;
        void fetchSelectedModelParameters(selectedModel.id);
        // void fetchModelById(selectedModel.id); // This doesn't do anything different for the time being.
    }

    function getAvailableRemoteModels(task: string): void {
        void fetchAvailableModels(task);
    }

    async function fetchAvailableModels(task: string): Promise<void> {
        try {
            setLoading(current => {return {...current, availableModels: true}} )
            const result = await getAvailableModels(task, AVAILABLE_MODELS_LIMIT);
            setAvailableModels(result);
        } catch(error) {            
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching available models:", error);
        } finally {                
            setLoading(current => {return {...current, availableModels: false}} )
        }
    }

    // async function fetchModelById(modelId: string|number): Promise<void> {
    //     try {
    //         // setLoading(current => {return {...current, : true}} )
    //         const result = await getModelById(modelId);
    //         console.log("Model details:", result);
    //         console.log("Selected Model:", selectedModel);
    //     } catch(error) {            
    //         // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
    //         console.error("Error in fetching model:", error);
    //     } finally {                
    //         // setLoading(current => {return {...current, : false}} )
    //     }
    // }

    async function fetchSelectedModelParameters(modelId: string|number): Promise<void> {
        try {
            setLoading(current => {return {...current, currentModelParameters: true}} )
            const result = await getModelParametersById(modelId);
            setSelectedModelParameters(result);
            console.log("Model Parameters:", result);
        } catch(error) {            
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching selected model parameters:", error);
        } finally {                
            setLoading(current => {return {...current, currentModelParameters: false}} )
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
                refreshSelectedModel,
                sortModels,
                getAvailableRemoteModels,
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