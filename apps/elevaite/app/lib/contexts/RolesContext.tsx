"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState } from "react";
import { getAccounts, getOrganization, getProjects } from "../actions/rbacActions";
import type { AccountObject, OrganizationObject, ProjectObject } from "../interfaces";


// STATIC OBJECTS


const defaultLoadingList: LoadingListObject = {
    organization: false,
    accounts: false,
    projects: false,
};


// INTERFACES

interface LoadingListObject {
    organization: boolean;
    accounts: boolean;
    projects: boolean;
}








// STRUCTURE 

export interface RolesContextStructure {
    organization: OrganizationObject|undefined;
    accounts: AccountObject[]|undefined;
    projects: ProjectObject[];
    selectedProject: ProjectObject|undefined;
    loading: LoadingListObject;
}


export const RolesContext = createContext<RolesContextStructure>({
    organization: undefined,
    accounts: undefined,
    projects: [],
    selectedProject: undefined,
    loading: defaultLoadingList,
});




// PROVIDER

interface RolesContextProviderProps {
    children: React.ReactNode;
}

export function RolesContextProvider(props: RolesContextProviderProps): JSX.Element {
    const session = useSession();
    const [organization, setOrganization] = useState<OrganizationObject|undefined>();
    const [accounts, setAccounts] = useState<AccountObject[]|undefined>();
    const [projects, setProjects] = useState<ProjectObject[]>([]);
    const [selectedProject, setSelectedProject] = useState<ProjectObject|undefined>();
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);

    
    useEffect(() => {
        if (session.data?.authToken) {
            void fetchOrganization(session.data.authToken);
            void fetchAccounts(session.data.authToken);
        }
    }, []);

    useEffect(() => {
        if (session.data?.authToken && accounts?.[0]) {
            void fetchProjects(accounts[0].id, session.data.authToken);
        }
    }, [accounts]);

    useEffect(() => {
        if (projects.length > 0) {
            const defaultProject = projects.find(project => project.name.toLowerCase() === "default project");
            if (defaultProject) {
                setSelectedProject(defaultProject);
            }
        }
    }, [projects]);




    async function fetchOrganization(authToken: string): Promise<void> {
        try {
            setLoading(current => {return {...current, organization: true}} );
            const fetchedOrganization = await getOrganization(authToken);
            setOrganization(fetchedOrganization);
        } catch (error) {            
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching organization:", error);
        } finally {            
            setLoading(current => {return {...current, organization: false}} )
        }
    }

    async function fetchAccounts(authToken: string): Promise<void> {
        try {
            setLoading(current => {return {...current, accounts: true}} );
            const fetchedAccounts = await getAccounts(authToken);
            setAccounts(fetchedAccounts);
        } catch (error) {            
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching accounts:", error);
        } finally {            
            setLoading(current => {return {...current, accounts: false}} )
        }
    }

    async function fetchProjects(accountId: string, authToken: string): Promise<void> {
        try {
            setLoading(current => {return {...current, projects: true}} );
            const fetchedProjects = await getProjects(accountId, authToken);
            setProjects(fetchedProjects);
        } catch (error) {            
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in fetching projects:", error);
        } finally {            
            setLoading(current => {return {...current, projects: false}} )
        }
    }











    return(
        <RolesContext.Provider
            value={ {
                organization,
                accounts,
                projects,
                selectedProject,
                loading,
            } }
        >
            {props.children}
        </RolesContext.Provider>
    )
}


export function useRoles(): RolesContextStructure {
    return useContext(RolesContext);
}

