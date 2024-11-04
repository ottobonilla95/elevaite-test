"use client";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { CreateProject, deleteContract, DeleteProject, EditProject, getContractObjectEmphasis, getContractObjectLineItems, getContractObjectVerification, getContractProjectById, getContractProjectContracts, getContractProjectSettings, getContractProjectsList, reprocessContract, submitContract } from "../actions/contractActions";
import { useInterval } from "../hooks";
import { ContractStatus, ContractObjectEmphasis, ContractObjectVerification, ContractObjectVerificationLineItem, ContractSettings, ContractVariations, ProjectObject, type CONTRACT_TYPES, type ContractExtractionDictionary, type ContractObject, type ContractProjectObject } from "../interfaces";




const REFETCH_TIME_IN_MILLISECONDS = 10000;



// STATIC OBJECTS

const defaultLoadingList: LoadingListObject = {
    projects: undefined,
    contracts: undefined,
    submittingContract: false,
    deletingContract: false,
    projectReports: {},
    projectSettings: {},
    contractEmphasis: {},
    contractLineItems: {},
    contractVerification: {},
};



// INTERFACES

interface LoadingListObject {
    projects: boolean|undefined;
    contracts: boolean|undefined;
    submittingContract: boolean;
    deletingContract: boolean;
    projectReports: Record<string, boolean>;
    projectSettings: Record<string, boolean>;
    contractEmphasis: Record<string, boolean>;
    contractLineItems: Record<string, boolean>;
    contractVerification: Record<string, boolean>;
}





// STRUCTURE 

export interface ContractsContextStructure {
    projects: ContractProjectObject[];
    selectedProject: ContractProjectObject|undefined;
    setSelectedProjectById: (id: string|number|undefined) => void;
    selectedContract: ContractObject | undefined;
    setSelectedContract: (contract: ContractObject|undefined) => void;
    setSelectedContractById: (id: string|number|undefined) => void;
    secondarySelectedContract: ContractObject|CONTRACT_TYPES|undefined;
    setSecondarySelectedContract: (contract: ContractObject|CONTRACT_TYPES|undefined) => void;
    setSecondarySelectedContractById: (id: string|number|undefined) => void;
    getContractById: (id: string|number) => ContractObject|undefined;
    reprocessSelectedContract: () => void;
    changeSelectedContractBit: (pageKey: `page_${number}`, itemKey: string, newValue: string) => void;
    changeSelectedContractTableBit: (pageKey: `page_${number}`, tableKey: string, newTableData: Record<string, string>[]) => void;
    submitCurrentContractPdf: (pdf: File|undefined, type: CONTRACT_TYPES, projectId: string|number, name?: string) => void;
    deleteContract: (projectId: string, contractId: string) => Promise<boolean>; 
    createProject: (name: string, description?: string) => Promise<boolean>;
    editProject: (projectId: string, name: string, description?: string) => Promise<boolean>;
    deleteProject: (projectId: string) => Promise<boolean>;
    loading: LoadingListObject;
}



export const ContractsContext = createContext<ContractsContextStructure>({
    projects: [],
    selectedProject: undefined,
    setSelectedProjectById: () => {/**/},
    selectedContract: undefined,
    setSelectedContract: () => {/**/},
    setSelectedContractById: () => {/**/},
    secondarySelectedContract: undefined,
    setSecondarySelectedContract: () => {/**/},
    setSecondarySelectedContractById: () => {/**/},
    getContractById: () => undefined,
    reprocessSelectedContract: () => {/**/},
    changeSelectedContractBit: () => {/**/},
    changeSelectedContractTableBit: () => {/**/},
    submitCurrentContractPdf: () => undefined,
    deleteContract: async () => { return false; },
    // eslint-disable-next-line @typescript-eslint/require-await -- We don't need to await for the core structure.
    createProject: async () => { return false; },
    editProject: async () => { return false; },
    deleteProject: async () => { return false; },
    loading: defaultLoadingList,
});




// FUNCTIONS









// PROVIDER

interface ContractsContextProviderProps {
    variation: ContractVariations;
    children: React.ReactNode;
}


export function ContractsContextProvider(props: ContractsContextProviderProps): JSX.Element {
    const variation = props.variation;
    const [projects, setProjects] = useState<ContractProjectObject[]>([]);
    const [selectedProject, setSelectedProject] = useState<ContractProjectObject|undefined>();
    const [selectedContract, setSelectedContract] = useState<ContractObject|undefined>();
    const [secondarySelectedContract, setSecondarySelectedContract] = useState<ContractObject|CONTRACT_TYPES|undefined>();
    const [processedContract, setProcessedContract] = useState<{id: string, data: ContractObject}|undefined>();
    const [hasCurrentContractFailed, setHasCurrentContractFailed] = useState("");
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);    
    const selectedContractChangedByUser = useRef<boolean>();
    const updateSelectedContract = useRef<string|number|undefined>();
    const updateSecondarySelectedContract = useRef<string|number|undefined>();

    

    // useInterval(() => { 
        // void actionFetchProjectsList(true);
    //  }, REFETCH_TIME_IN_MILLISECONDS);


    useEffect(() => {
        void actionFetchProjectsList();
    }, []);

    useEffect(() => {
        // console.log("Projects", projects);
        if (!selectedProject) return;
        const newSelection = projects.find(item => item.id === selectedProject.id);
        setSelectedProject(newSelection);
        if (updateSelectedContract.current) {
            if (selectedContract) setSelectedContractById(updateSelectedContract.current);
            updateSelectedContract.current = undefined;
        }
        if (updateSecondarySelectedContract.current) {
            if (secondarySelectedContract) setSecondarySelectedContractById(updateSecondarySelectedContract.current);
            updateSecondarySelectedContract.current = undefined;
        }
    }, [projects]);


    useEffect(() => {
        if (!selectedProject) return;
        fetchProjectDetails(selectedProject);

        if (!selectedProject.reports || !selectedContract) return;
        const foundSelectedContract = selectedProject.reports.find(contract => contract.id === selectedContract.id);
        if (foundSelectedContract) {
            if (foundSelectedContract.status !== selectedContract.status) {
                setSelectedContractById(foundSelectedContract.id);
            }
        }
    }, [selectedProject]);


    useEffect(() => {
        if (!selectedContract) return;
        console.log("Selected Contract", selectedContract);
        fetchContractDetails(selectedContract);
    }, [selectedContract]);

    useEffect(() => {
        if (!secondarySelectedContract || typeof secondarySelectedContract !== "object") return;
        fetchContractDetails(secondarySelectedContract, true);
    }, [secondarySelectedContract]);


    useEffect(() => {       
        if (!processedContract) return;
        replaceTemporaryContractWithProcessed(processedContract.id, processedContract.data);
    }, [processedContract]);


    useEffect(() => {
        if (!hasCurrentContractFailed) return;
        changeStatusToContractInList(hasCurrentContractFailed, ContractStatus.ExtractionFailed);
    }, [hasCurrentContractFailed]);



    





    // Data handling - getting or updating information on the projectsList and selected items

    function getContractById(id: string|number): ContractObject | undefined {
        return projects.flatMap(project => project.reports ?? []).find(contract => contract.id === id);
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
        const foundContract = projects.flatMap(project => project.reports ?? []).find(contract => contract.id.toString() === id.toString());
        if (foundContract) setSelectedContract(foundContract);
    }

    function setSecondarySelectedContractById(id: string|number|undefined): void {
        if (projects.length === 0) return;
        if (id === undefined) {
            setSecondarySelectedContract(undefined);
            return;
        }
        const foundContract = projects.flatMap(project => project.reports ?? []).find(contract => contract.id.toString() === id.toString());
        if (foundContract) setSecondarySelectedContract(foundContract);
    }

    function replaceProject(newProject: ContractProjectObject): void {
        setProjects((prevProjects) =>
            prevProjects.map((project) => project.id === newProject.id ? newProject : project)
        );
    }

    function appendSettingsOnProject(id: string|number, settings: ContractSettings): void {
        setProjects(currentProjects => 
                currentProjects.map(project => 
                    project.id === id ? {...project, settings: settings} : project
                )
        );
    }

    function appendReportsOnProject(id: string|number, reports: ContractObject[]): void {
        setProjects(currentProjects => 
                currentProjects.map(project => 
                    project.id === id ? {...project, reports: reports} : project
                )
        );
    }

    function appendEmphasisOnContract(projectId: string, contractId: string, emphasis: ContractObjectEmphasis, secondary?: boolean): void {
        if (secondary) updateSecondarySelectedContract.current = contractId;
        else updateSelectedContract.current = contractId;
        setProjects(currentProjects => 
            currentProjects.map(project =>
                project.id.toString() !== projectId ? project :
                {...project,
                    reports: project.reports?.map(report => 
                        report.id.toString() !== contractId ? report :
                        {...report, highlight: emphasis}
                    )
                }
            )
        );
    }

    function appendLineItemsOnContract(projectId: string, contractId: string, lineItems: ContractObjectVerificationLineItem[], secondary?: boolean): void {     
        if (secondary) updateSecondarySelectedContract.current = contractId;
        else updateSelectedContract.current = contractId;   
        setProjects(currentProjects => 
            currentProjects.map(project =>
                project.id.toString() !== projectId ? project :
                {...project,
                    reports: project.reports?.map(report => 
                        report.id.toString() !== contractId ? report :
                        {...report, line_items: lineItems}
                    )
                }
            )
        );
    }

    function appendVerificationOnContract(projectId: string, contractId: string, verification: ContractObjectVerification, secondary?: boolean): void {
        if (secondary) updateSecondarySelectedContract.current = contractId;
        else updateSelectedContract.current = contractId;
        setProjects(currentProjects => 
            currentProjects.map(project =>
                project.id.toString() !== projectId ? project :
                {...project,
                    reports: project.reports?.map(report => 
                        report.id.toString() !== contractId ? report :
                        {...report, verification: verification}
                    )
                }
            )
        );
    }
    
    function replaceTemporaryContractWithProcessed(id: string, data: ContractObject): void {
        // If the returned data's id exists, replace it, then delete the previous id.
        const existingReport = projects.flatMap(project => project.reports).find(contract => contract?.id === data.id);
        updateSelectedContract.current = data.id;

        if (existingReport) {
            // Replace the data of the original report (data.id)
            setProjects((currentProjects) =>
                currentProjects.map((project) => ({
                    ...project,
                    reports: project.reports?.map((report) =>
                        report.id === data.id ? data : report
                    ),
                }))
            );
            // Delete the temporary line item (id)
            setProjects((prevProjects) =>
                prevProjects.map((project) => ({
                    ...project,
                    reports: project.reports?.filter((report) => report.id !== id),
                }))
            );
        }

        // Otherwise, replace the previous id with the new item
        setProjects((currentProjects) =>
            currentProjects.map((project) => ({
                ...project,
                reports: project.reports?.map((report) =>
                    report.id === id ? data : report
                ),
            }))
        );
    }

    function changeStatusToContractInList(id: string, status: ContractStatus): void {
        setProjects((currentProjects) =>
            currentProjects.map((project) => ({
                ...project,
                reports: project.reports?.map((report) =>
                    report.id === id ? { ...report, status } : report
                ),
            }))
        );
    }

    
    // Fetching convenience handlers

    function fetchProjectDetails(passedProject: ContractProjectObject): void {
        if (passedProject.settings === null) void actionFetchProjectSettings(passedProject.id);
        if (passedProject.reports === null) void actionFetchProjectReports(passedProject.id);
    }

    function fetchContractDetails(passedContract: ContractObject, secondary?: boolean): void {
        if (passedContract.highlight === null) void actionFetchContractEmphasis(passedContract.project_id, passedContract.id, secondary);
        if (passedContract.verification === null) void actionFetchContractVerification(passedContract.project_id, passedContract.id, secondary);
        if (passedContract.line_items === null) void actionFetchContractLineItems(passedContract.project_id, passedContract.id, secondary);
    }


    // Contract details editing - only front-end for now.

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



    // Misc

    function submitCurrentContractPdf(pdf: File|undefined, type: CONTRACT_TYPES, projectId: string|number, name?: string): void {;
        if (pdf) { void actionSubmitContract(pdf, type, projectId, name); }
    }

    function appendContractToContractsList(project: ContractProjectObject, pdf: File, type: CONTRACT_TYPES, name?: string): string {
        const id = `NewContract_${project.id.toString()}_${((project.reports?.length ?? 0) + 1).toString()}`;

        const newContract: ContractObject = {
            id,
            project_id: selectedProject?.id ?? "none",
            status: ContractStatus.Extracting,
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
                    { ...currentProject, reports: [...(currentProject.reports || []), newContract] }
                    : currentProject
            )
        );
        return id;
    }





    // Actions - Create / Edit


    async function actionSubmitContract(submittedPdf: File, type: CONTRACT_TYPES, projectId: string|number, name?: string): Promise<void> {
        if (!selectedProject) return;
        setHasCurrentContractFailed("");
        const idOfNewEntry = appendContractToContractsList(selectedProject, submittedPdf, type, name);
        try {
            setLoading(current => { return {...current, submittingContract: true}} );
            const formData = new FormData();
            formData.append("file", submittedPdf);
            if (name) formData.append("label", name);
            const contractExtractionResults = await submitContract(projectId.toString(), formData, type, variation === ContractVariations.Iopex);
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

    async function actionDeleteContract(projectId: string, contractId: string): Promise<boolean> {
        try {
            setLoading(current => { return {...current, deletingContract: true}} );
            const contractDeletionResults = await deleteContract(contractId, projectId, variation === ContractVariations.Iopex);
            setProjects(current => current.map(project => project.id.toString() !== projectId ? project :
                {...project, 
                    reports: project.reports?.filter(report => report.id !== contractDeletionResults.id) ?? [],
                }
            ))
            return true;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in deleting contract:", error);
            return false;
        } finally {
            setLoading(current => { return {...current, deletingContract: false}} );
        }
    }

    async function actionCreateProject(name: string, description?: string): Promise<boolean> {
        try {
            setLoading(current => { return {...current, projects: true}} );
            
            const createProjectResult = await CreateProject(name, variation === ContractVariations.Iopex, description);
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

    async function actionEditProject(id: string, name: string, description?: string): Promise<boolean> {
        try {
            setLoading(current => { return {...current, projects: true}} );
            
            const editProjectResult = await EditProject(id, name, variation === ContractVariations.Iopex, description);
            setProjects(current => current.map(project => project.id === editProjectResult.id ? editProjectResult : project));
            return true;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in editing contract project:", error);
            return false;
        } finally {
            setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionDeleteProject(id: string): Promise<boolean> {
        try {
            setLoading(current => { return {...current, projects: true}} );
            
            const deleteProjectResult = await DeleteProject(id, variation === ContractVariations.Iopex);
            setProjects(current => current.filter(project => project.id !== deleteProjectResult.id));
            return true;
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in deleting contract project:", error);
            return false;
        } finally {
            setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionReprocessContract(): Promise<void> {
        if (!selectedProject || !selectedContract) return;
        try {
            // Stealth reprocess            
            const reprocessResult = await reprocessContract(selectedProject.id.toString(), selectedContract.id.toString(), variation === ContractVariations.Iopex);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in reprocessing contract:", error);
        }
    }



    // Actions - Fetching

    async function actionFetchProjectsList(noLoading?: boolean): Promise<void> {
        try {
            if (!noLoading) setLoading(current => { return {...current, projects: true}} );
            
            const projectsListResults = await getContractProjectsList(variation === ContractVariations.Iopex);
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
            const projectResult = await getContractProjectById(id.toString(), variation === ContractVariations.Iopex);
            replaceProject(projectResult);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract projects:", error);
        } finally {
            // setLoading(current => { return {...current, projects: false}} );
        }
    }

    async function actionFetchProjectSettings(id: string|number): Promise<void> {
        try {
            setLoading(current => { return {...current, projectSettings: { ...current.projectSettings, [id]: true } }})
            const projectSettingsResult = await getContractProjectSettings(id.toString(), variation === ContractVariations.Iopex);
            appendSettingsOnProject(id, projectSettingsResult);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching projects's settings:", error);
        } finally {
            setLoading(current => { return {...current, projectSettings: { ...current.projectSettings, [id]: false } }})
        }
    }

    async function actionFetchProjectReports(id: string|number): Promise<void> {
        try {
            setLoading(current => { return {...current, projectReports: { ...current.projectReports, [id]: true } }})
            const projectReportsResult = await getContractProjectContracts(id.toString(), variation === ContractVariations.Iopex);
            appendReportsOnProject(id, projectReportsResult);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching projects's reports:", error);
        } finally {
            setLoading(current => { return {...current, projectReports: { ...current.projectReports, [id]: false } }})
        }
    }

    async function actionFetchContractEmphasis(projectId: string|number, id: string|number, secondary?: boolean): Promise<void> {
        try {
            setLoading(current => { return {...current, contractEmphasis: { ...current.contractEmphasis, [id]: true } }})
            const contractEmphasisResult = await getContractObjectEmphasis(projectId.toString(), id.toString(), variation === ContractVariations.Iopex);
            appendEmphasisOnContract(projectId.toString(), id.toString(), contractEmphasisResult, secondary);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract's emphasis:", error);
        } finally {
            setLoading(current => { return {...current, contractEmphasis: { ...current.contractEmphasis, [id]: false } }})
        }
    }

    async function actionFetchContractVerification(projectId: string|number, id: string|number, secondary?: boolean): Promise<void> {
        try {
            setLoading(current => { return {...current, contractVerification: { ...current.contractVerification, [id]: true } }})
            const contractVerificationResult = await getContractObjectVerification(projectId.toString(), id.toString(), variation === ContractVariations.Iopex);
            appendVerificationOnContract(projectId.toString(), id.toString(), contractVerificationResult, secondary);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract's verification:", error);
        } finally {
            setLoading(current => { return {...current, contractVerification: { ...current.contractVerification, [id]: false } }})
        }
    }

    async function actionFetchContractLineItems(projectId: string|number, id: string|number, secondary?: boolean): Promise<void> {
        try {
            setLoading(current => { return {...current, contractLineItems: { ...current.contractLineItems, [id]: true } }})
            const contractLineItemsResult = await getContractObjectLineItems(projectId.toString(), id.toString(), variation === ContractVariations.Iopex);
            appendLineItemsOnContract(projectId.toString(), id.toString(), contractLineItemsResult, secondary);
        } catch(error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching contract's line items:", error);
        } finally {
            setLoading(current => { return {...current, contractLineItems: { ...current.contractLineItems, [id]: false } }})
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
                secondarySelectedContract,
                setSecondarySelectedContract,
                setSecondarySelectedContractById,
                getContractById,
                reprocessSelectedContract: actionReprocessContract,
                changeSelectedContractBit,
                changeSelectedContractTableBit,
                submitCurrentContractPdf,
                deleteContract: actionDeleteContract,
                createProject: actionCreateProject,
                editProject: actionEditProject,
                deleteProject: actionDeleteProject,
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