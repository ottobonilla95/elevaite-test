"use client";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { CreateProject, getContractProjectById, getContractProjectsList, reprocessContract, submitContract } from "../actions/contractActions";
import { CONTRACT_STATUS, type CONTRACT_TYPES, type ContractExtractionDictionary, type ContractObject, type ContractProjectObject } from "../interfaces";




const REFETCH_TIME_IN_MILLISECONDS = 10000;



// STATIC OBJECTS

const defaultLoadingList: LoadingListObject = {
    projects: undefined,
    contracts: undefined,
    submittingContract: false,
};



// INTERFACES

interface LoadingListObject {
    projects: boolean|undefined;
    contracts: boolean|undefined;
    submittingContract: boolean;
}





// STRUCTURE 

export interface ContractsContextStructure {
    projects: ContractProjectObject[];
    selectedProject: ContractProjectObject|undefined;
    setSelectedProjectById: (id: string|number|undefined) => void;
    selectedContract: ContractObject | undefined;
    setSelectedContract: (contract: ContractObject|undefined) => void;
    setSelectedContractById: (id: string|number|undefined) => void;
    reprocessSelectedContract: () => void;
    changeSelectedContractBit: (pageKey: `page_${number}`, itemKey: string, newValue: string) => void;
    changeSelectedContractTableBit: (pageKey: `page_${number}`, tableKey: string, newTableData: Record<string, string>[]) => void;
    submitCurrentContractPdf: (pdf: File|undefined, type: CONTRACT_TYPES, projectId: string|number, name?: string) => void;
    createProject: (name: string, description?: string) => Promise<boolean>;
    loading: LoadingListObject;
}



export const ContractsContext = createContext<ContractsContextStructure>({
    projects: [],
    selectedProject: undefined,
    setSelectedProjectById: () => {/**/},
    selectedContract: undefined,
    setSelectedContract: () => {/**/},
    setSelectedContractById: () => {/**/},
    reprocessSelectedContract: () => {/**/},
    changeSelectedContractBit: () => {/**/},
    changeSelectedContractTableBit: () => {/**/},
    submitCurrentContractPdf: () => undefined,
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    createProject: async () => { return false; },
    loading: defaultLoadingList,
});




// FUNCTIONS









// PROVIDER

interface ContractsContextProviderProps {
    children: React.ReactNode;
}


export function ContractsContextProvider(props: ContractsContextProviderProps): JSX.Element {
    const [projects, setProjects] = useState<ContractProjectObject[]>([]);
    const [selectedProject, setSelectedProject] = useState<ContractProjectObject|undefined>();
    const [selectedContract, setSelectedContract] = useState<ContractObject|undefined>();
    const [processedContract, setProcessedContract] = useState<{id: string, data: ContractObject}|undefined>();
    const [hasCurrentContractFailed, setHasCurrentContractFailed] = useState("");
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);
    
    const selectedContractChangedByUser = useRef<boolean>();
    const updateSelectedContract = useRef<string|number|undefined>();



    useInterval(() => { 
        void actionFetchProjectsList(true);
     }, REFETCH_TIME_IN_MILLISECONDS);


    useEffect(() => {
        void actionFetchProjectsList();
    }, []);

    useEffect(() => {
        if (!selectedProject) return;
        const newSelection = projects.find(item => item.id === selectedProject.id);
        setSelectedProject(newSelection);
        if (updateSelectedContract.current) {
            if (selectedContract) setSelectedContractById(updateSelectedContract.current);
            updateSelectedContract.current = undefined;
        }
    }, [projects]);


    useEffect(() => {
        if (!selectedProject || !selectedContract) return;
        const foundSelectedContract = selectedProject.reports.find(contract => contract.id === selectedContract.id);
        if (foundSelectedContract) {
            if (foundSelectedContract.status !== selectedContract.status) {
                setSelectedContractById(foundSelectedContract.id);
            }
        }
    }, [selectedProject]);

    useEffect(() => {
        if (selectedContract)
            console.log("Selected Contract", selectedContract);
    }, [selectedContract]);


    useEffect(() => {       
        if (!processedContract) return;
        replaceTemporaryContractWithProcessed(processedContract.id, processedContract.data);
    }, [processedContract]);


    useEffect(() => {
        if (!hasCurrentContractFailed) return;
        changeStatusToContractInList(hasCurrentContractFailed, CONTRACT_STATUS.FAILED);
    }, [hasCurrentContractFailed]);



    
    function useInterval(callback: () => void, delay: number): void {
        const savedCallback = useRef<() => void>();      
        // Remember the latest callback.
        useEffect(() => {
            savedCallback.current = callback;
        }, [callback]);
      
        // Set up the interval.
        useEffect(() => {
            function tick(): void {
                if (savedCallback.current) {
                    savedCallback.current();
                }
            }
          const intervalId = setInterval(tick, delay);
          return () => { clearInterval(intervalId); };
        }, [delay]);
    }






    function setSelectedProjectById(id: string|number|undefined): void {
        if (projects.length === 0) return;
        if (id === undefined) {
            setSelectedProject(undefined);
            return;
        }
        const foundProject = projects.find(item => item.id === id);
        if (foundProject) setSelectedProject(foundProject);
    }

    function setSelectedContractById(id: string|number|undefined): void {
        if (projects.length === 0) return;
        if (id === undefined) {
            setSelectedContract(undefined);
            return;
        }
        const foundContract = projects.flatMap(project => project.reports).find(contract => contract.id === id);
        if (foundContract) setSelectedContract(foundContract);
    }

    function changeSelectedContractBit(pageKey: `page_${number}`, itemKey: string, newValue: string): void {
        selectedContractChangedByUser.current = true;
        setSelectedContract(current => { 
            if (!current) return;
            const oldData = current.response;
            const newData: ContractExtractionDictionary|null = oldData === null ? null : {
                ...oldData,
                [pageKey]: {
                    ...oldData[pageKey],
                    [itemKey]: newValue
                }
            };
            return {...current, extractedData: newData};
        });
    }

    function changeSelectedContractTableBit(pageKey: `page_${number}`, tableKey: string, newTableData: Record<string, string>[]): void {
        selectedContractChangedByUser.current = true;
        setSelectedContract(current => { 
            if (!current) return;
            const oldData = current.response;
            const newData: ContractExtractionDictionary|null = oldData === null ? null : {
                ...oldData,
                [pageKey]: {
                    ...oldData[pageKey],
                    [tableKey]: newTableData
                }
            };
            return {...current, extractedData: newData};
        });
    }




    function submitCurrentContractPdf(pdf: File|undefined, type: CONTRACT_TYPES, projectId: string|number, name?: string): void {;
        if (pdf) {
            void actionSubmitContract(pdf, type, projectId, name);
        }
    }

    function appendContractToContractsList(project: ContractProjectObject, pdf: File, type: CONTRACT_TYPES, name?: string): string {
        const id = `NewContract_${project.id.toString()}_${(project.reports.length + 1).toString()}`;

        const newContract: ContractObject = {
            id,
            project_id: selectedProject?.id ?? "none",
            status: CONTRACT_STATUS.PROCESSING,
            content_type: type,
            label: name,
            filename: pdf.name,
            filesize: pdf.size,
            file_ref: pdf,
            response: null,
            tags: [],
            creation_date: new Date().toISOString(),
            checksum: "",
        }

        setProjects((prevProjects) =>
            prevProjects.map((currentProject) =>
                currentProject.id === project.id ?
                    { ...currentProject, reports: [...currentProject.reports, newContract] }
                    : currentProject
            )
        );
        return id;
    }

    function replaceProject(newProject: ContractProjectObject): void {
        setProjects((prevProjects) =>
            prevProjects.map((project) => project.id === newProject.id ? newProject : project)
        );
    }

    function replaceTemporaryContractWithProcessed(id: string, data: ContractObject): void {
        // If the returned data's id exists, replace it, then delete the previous id.
        const existingReport = projects.flatMap(project => project.reports).find(contract => contract.id === data.id);
        updateSelectedContract.current = data.id;

        if (existingReport) {
            // Replace the data of the original report (data.id)
            setProjects((currentProjects) =>
                currentProjects.map((project) => ({
                    ...project,
                    reports: project.reports.map((report) =>
                        report.id === data.id ? data : report
                    ),
                }))
            );
            // Delete the temporary line item (id)
            setProjects((prevProjects) =>
                prevProjects.map((project) => ({
                    ...project,
                    reports: project.reports.filter((report) => report.id !== id),
                }))
            );
        }

        // Otherwise, replace the previous id with the new item
        setProjects((currentProjects) =>
            currentProjects.map((project) => ({
                ...project,
                reports: project.reports.map((report) =>
                    report.id === id ? data : report
                ),
            }))
        );
    }

    function changeStatusToContractInList(id: string, status: CONTRACT_STATUS): void {
        setProjects((currentProjects) =>
            currentProjects.map((project) => ({
                ...project,
                reports: project.reports.map((report) =>
                    report.id === id ? { ...report, status } : report
                ),
            }))
        );
    }




    async function actionSubmitContract(submittedPdf: File, type: CONTRACT_TYPES, projectId: string|number, name?: string): Promise<void> {
        if (!selectedProject) return;
        setHasCurrentContractFailed("");
        const idOfNewEntry = appendContractToContractsList(selectedProject, submittedPdf, type, name);
        try {
            setLoading(current => { return {...current, submittingContract: true}} );
            const formData = new FormData();
            formData.append("file", submittedPdf);
            if (name) formData.append("label", name);
            const contractExtractionResults = await submitContract(projectId.toString(), formData, type);
            setProcessedContract({id: idOfNewEntry, data: contractExtractionResults});
            await actionFetchProjectById(projectId);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in submitting contract:", error);
            setHasCurrentContractFailed(idOfNewEntry);
        } finally {
            setLoading(current => { return {...current, submittingContract: false}} );
        }
    }

    async function actionReprocessContract(): Promise<void> {
        if (!selectedProject || !selectedContract) return;
        try {
            // Stealth reprocess            
            const reprocessResult = await reprocessContract(selectedProject.id.toString(), selectedContract.id.toString());
            console.log("Reprocessing result");
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in reprocessing contract:", error);
        }
    }

    async function actionCreateProject(name: string, description?: string): Promise<boolean> {
        try {
            setLoading(current => { return {...current, projects: true}} );
            
            const createProjectResult = await CreateProject(name, description);
            setProjects(current => [...current, createProjectResult]);
            return true;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in creating contract project:", error);
            return false;
        } finally {
            setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionFetchProjectsList(noLoading?: boolean): Promise<void> {
        try {
            if (!noLoading) setLoading(current => { return {...current, projects: true}} );
            
            const projectsListResults = await getContractProjectsList();
            setProjects(projectsListResults);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract projects:", error);
        } finally {
            if (!noLoading) setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionFetchProjectById(id: string|number): Promise<void> {
        try {
            // setLoading(current => { return {...current, projects: true}} );
            // Stealth update            
            const projectResult = await getContractProjectById(id.toString());
            replaceProject(projectResult);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract projects:", error);
        } finally {
            // setLoading(current => { return {...current, projects: false}} );
        }
    }







  
    return (
        <ContractsContext.Provider
            value={ {
                projects,
                selectedProject,
                setSelectedProjectById,
                selectedContract,
                setSelectedContract,
                setSelectedContractById,
                reprocessSelectedContract: actionReprocessContract,
                changeSelectedContractBit,
                changeSelectedContractTableBit,
                submitCurrentContractPdf,
                createProject: actionCreateProject,
                loading,
            } }
        >
            {props.children}
        </ContractsContext.Provider>
    );
}

  
export function useContracts(): ContractsContextStructure {
    return useContext(ContractsContext);
}