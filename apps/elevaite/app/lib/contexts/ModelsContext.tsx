"use client";
import { createContext, useContext, useState } from "react";
import type { ModelObject} from "../interfaces";
import { ModelsStatus } from "../interfaces";


const TEST: ModelObject[] = [
    {
        id: "Test_1",
        date_created: new Date().toISOString(),
        model_type: "question-answering",
        name: "Test model 1",
        status: ModelsStatus.ACTIVE,
        tags: ["Test Tag 1", "Test Tag 2"],
        node: {
            cpu: 8,
            gpu: 1,
            ram: 48,
        }
    },
    {
        id: "Test_2",
        date_created: new Date().toISOString(),
        model_type: "question-answering",
        name: "Test model 2",
        status: ModelsStatus.REGISTERING,
        tags: ["Test Tag 1", "Test Tag 2", "Test Tag 3", "Test Tag 4"],
        node: {
            cpu: 8,
            gpu: 1,
            ram: 96,
        }
    },
    {
        id: "Test_3",
        date_created: new Date().toISOString(),
        model_type: "token-classification",
        name: "Test model 3",
        status: ModelsStatus.FAILED,
        tags: ["Test Tag 1"],
        node: {
            cpu: 4,
            gpu: 1,
            ram: 24,
        }
    },
];


// STRUCTURE 

export interface ModelsContextStructure {
    models: ModelObject[];
}


export const ModelsContext = createContext<ModelsContextStructure>({
    models: [],
});





// PROVIDER

interface ModelsContextProviderProps {
    children: React.ReactNode;
}


export function ModelsContextProvider(props: ModelsContextProviderProps): JSX.Element {
    const [displayModels, setDisplayModels] = useState<ModelObject[]>(TEST);

  
    return (
        <ModelsContext.Provider
            value={ {
                models: displayModels,
            } }
        >
            {props.children}
        </ModelsContext.Provider>
    );
}
  
export function useModels(): ModelsContextStructure {
    return useContext(ModelsContext);
}