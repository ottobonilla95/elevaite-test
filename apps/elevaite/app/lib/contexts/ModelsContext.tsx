"use client";
import { createContext, useContext, useEffect, useState } from "react";
import dayjs from "dayjs";
import type { ModelObject} from "../interfaces";
import { ModelsStatus } from "../interfaces";


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
        date_created: dayjs().toISOString(),
        model_type: "question-answering",
        name: "Test model 1",
        status: ModelsStatus.ACTIVE,
        tags: ["Test Tag 1", "Test Tag 2"],
        ramToRun: "24 GB",
        ramToTrain: "80 GB",
        node: {
            cpu: 8,
            gpu: 1,
            ram: 48,
        }
    },
    {
        id: "Test_2",
        date_created: dayjs().subtract(1, "hour").toISOString(),
        model_type: "question-answering",
        name: "Test model 2",
        status: ModelsStatus.REGISTERING,
        tags: ["Test Tag 1", "Test Tag 2", "Test Tag 3", "Test Tag 4"],
        ramToRun: "24 GB",
        ramToTrain: "64 GB",
        node: {
            cpu: 8,
            gpu: 1,
            ram: 96,
        }
    },
    {
        id: "Test_3",
        date_created: dayjs().subtract(15, "minutes").toISOString(),
        model_type: "token-classification",
        name: "Test model 3",
        status: ModelsStatus.FAILED,
        tags: [],
        ramToRun: "16 GB",
        ramToTrain: "24 GB",
        node: {
            cpu: 4,
            gpu: 1,
            ram: 24,
        }
    },
    {
        id: "Test_4",
        date_created: dayjs().subtract(1, "minute").toISOString(),
        model_type: "token-classification",
        name: "Test model 4",
        status: ModelsStatus.DEPLOYED,
        endpointUrl: "testURL",
        tags: ["Test Tag 1"],
        ramToRun: "24 GB",
        ramToTrain: "64 GB",
        node: {
            cpu: 4,
            gpu: 1,
            ram: 24,
        }
    },
];

// INTERFACES

interface SortingObject {
    field?: keyof ModelObject;
    isDesc?: boolean;
}


// STRUCTURE 

export interface ModelsContextStructure {
    models: ModelObject[];
    modelTasks: string[];
    modelsSorting: SortingObject;
    sortModels: (field: string, specialHandling?: string) => void;
}


export const ModelsContext = createContext<ModelsContextStructure>({
    models: [],
    modelTasks: [],
    modelsSorting: {field: undefined},
    sortModels: () => {/**/},
});





// FUNCTIONS

function sortDisplayModels(models: ModelObject[], sorting: SortingObject, specialHandling?: specialHandlingModelFields): ModelObject[] {    
    const statusSortOrder = [ModelsStatus.REGISTERING, ModelsStatus.FAILED, ModelsStatus.DEPLOYED, ModelsStatus.ACTIVE];

    switch (specialHandling) {
        case specialHandlingModelFields.STATUS: 
            models.sort((a,b) => statusSortOrder.indexOf(a.status) - statusSortOrder.indexOf(b.status));
            break;
        case specialHandlingModelFields.DATE:
            models.sort((a,b) => dayjs(a.date_created).valueOf() - dayjs(b.date_created).valueOf());
            break;
        case specialHandlingModelFields.TAGS:
            models.sort((a,b) => (a.tags.length > 0 === b.tags.length > 0)? 0 : a.tags.length > 0 ? -1 : 1);
            break;
        default:
            if (sorting.field) {
                models.sort((a,b) => {
                    if (sorting.field && typeof a[sorting.field] === "string" && typeof b[sorting.field] === "string" && !Array.isArray(a[sorting.field]) && !Array.isArray(b[sorting.field]))
                    return (a[sorting.field] as string).localeCompare(b[sorting.field] as string);
                    return 0;
                })
            } else {
                models.sort((a,b) => dayjs(a.date_created).valueOf() - dayjs(b.date_created).valueOf());
            }
    }

    if (sorting.isDesc) {
        models.reverse();
    }
    return models;
}


function getModelTasks(): string[] {
    return [
        "conversational",
        "document-question-answering",
        "question-answering",
        "summarization",
        "table-question-answering",
        "text2text-generation",
        "text-classification",
        "text-generation",
        "text-to-audio",
        "token-classification",
        "zero-shot-classification",
    ].sort();
}






// PROVIDER

interface ModelsContextProviderProps {
    children: React.ReactNode;
}


export function ModelsContextProvider(props: ModelsContextProviderProps): JSX.Element {
    const [models, setModels] = useState<ModelObject[]>(TEST);
    const [modelTasks, setModelTasks] = useState<string[]>([]);
    const [displayModels, setDisplayModels] = useState<ModelObject[]>([]);
    const [sorting, setSorting] = useState<SortingObject>({field: undefined});

    useEffect(() => {
        setModelTasks(getModelTasks());
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


  
    return (
        <ModelsContext.Provider
            value={ {
                models: displayModels,
                modelTasks,
                modelsSorting: sorting,
                sortModels,
            } }
        >
            {props.children}
        </ModelsContext.Provider>
    );
}
  
export function useModels(): ModelsContextStructure {
    return useContext(ModelsContext);
}