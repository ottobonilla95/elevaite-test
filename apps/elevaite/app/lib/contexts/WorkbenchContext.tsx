"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { type ApplicationObject, ApplicationType } from "../interfaces";
import { getApplicationList } from "../actions/applicationActions";






// STATIC OBJECTS


const defaultLoadingList: LoadingListObject = {
    applications: undefined,
};

const defaultErrorList: ErrorListObject = {
    applications: false,
}


// INTERFACES

interface LoadingListObject {
    applications: boolean|undefined;
}

interface ErrorListObject {
    applications: boolean;
}




// STRUCTURE 

export interface WorkbenchContextStructure {
    applicationList: ApplicationObject[];
    ingestList: ApplicationObject[];
    preProcessingList: ApplicationObject[];
    loading: LoadingListObject;
    errors: ErrorListObject;
}

export const WorkbenchContext = createContext<WorkbenchContextStructure>({
    applicationList: [],
    ingestList: [],
    preProcessingList: [],
    loading: defaultLoadingList,
    errors: defaultErrorList,
});





// PROVIDER

interface WorkbenchContextProviderProps {
    children: React.ReactNode;
}

export function WorkbenchContextProvider(props: WorkbenchContextProviderProps): JSX.Element {
    const [applicationList, setApplicationList] = useState<ApplicationObject[]>([]);
    const [ingestList, setIngestList] = useState<ApplicationObject[]>([]);
    const [preProcessingList, setPreProcessingList] = useState<ApplicationObject[]>([]);
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);
    const [errors, setErrors] = useState<ErrorListObject>(defaultErrorList);
    

    useEffect(() => {
        void fetchApplicationList();
    }, []);

    useEffect(() => {
        setIngestList(applicationList.filter((app) => { return app.applicationType === ApplicationType.INGEST; }));
        setPreProcessingList(applicationList.filter((app) => { return app.applicationType === ApplicationType.PREPROCESS; }));
    }, [applicationList]);




    async function fetchApplicationList(): Promise<void> {
        try {
            setLoading(current => {return {...current, applications: true}} );
            const data = await getApplicationList();
            setApplicationList(data);
            setErrors(current => {return { ...current, applications: false}} );
          } catch (error) {
            setErrors(current => {return { ...current, applications: true}} );
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error('Error fetching application list:', error);
          } finally {
            setLoading(current => {return {...current, applications: false}} );
          }
    }



  
    return (
        <WorkbenchContext.Provider
            value={ {
                applicationList,
                ingestList,
                preProcessingList,
                loading,
                errors,
            } }
        >
            {props.children}
        </WorkbenchContext.Provider>
    );
}
  
export function useWorkbench(): WorkbenchContextStructure {
    return useContext(WorkbenchContext);
}