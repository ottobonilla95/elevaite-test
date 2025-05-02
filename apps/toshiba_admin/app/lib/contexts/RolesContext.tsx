"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState } from "react";
import { ACCESS_MANAGEMENT_TABS, type AccountObject, type LoadingListObject, type OrganizationObject, type ProjectObject, type RoleObject, type UserObject } from "../interfaces";

// STATIC OBJECTS
const defaultLoadingList: LoadingListObject = {
    organization: true,
    accounts: true,
    projects: true,
    users: true,
    roles: true,
    addEditAccount: false,
    addEditProject: false,
    addEditUser: false,
    userProfile: {},
};

// STRUCTURE 
function simpleAsyncBoolean(): Promise<boolean> {
    return new Promise(resolve => {
        setTimeout(() => { resolve(false); }, 100);
    });
}

export interface RolesContextStructure {
    organization: OrganizationObject|undefined;
    users: UserObject[];
    editUser: (userId: string, firstName: string, lastName: string) => Promise<boolean>,
    getUserProfile: (userId: string) => Promise<UserObject|undefined>,
    roles: RoleObject[];
    accounts: AccountObject[]|undefined;
    addAccount: (accountName: string, accountDescription?: string) => Promise<boolean>,
    editAccount: (accountId: string, accountName: string, accountDescription?: string) => Promise<boolean>,
    addProject: (accountId: string, projectName: string, projectDescription?: string, parentProjectId?: string) => Promise<boolean>,
    editProject: (projectId: string, projectName: string, projectDescription?: string) => Promise<boolean>,
    projects: ProjectObject[];
    selectedProject: ProjectObject|undefined;
    refresh: (refreshType: ACCESS_MANAGEMENT_TABS) => void;
    loading: LoadingListObject;
}

export const RolesContext = createContext<RolesContextStructure>({
    organization: undefined,
    users: [],
    editUser: async () => { await simpleAsyncBoolean(); return false; },
    getUserProfile: async () => { await simpleAsyncBoolean(); return undefined; },
    roles: [],
    accounts: undefined,
    addAccount: async () => { await simpleAsyncBoolean(); return false; },
    editAccount: async () => { await simpleAsyncBoolean(); return false; },
    addProject: async () => { await simpleAsyncBoolean(); return false; },
    editProject: async () => { await simpleAsyncBoolean(); return false; },
    projects: [],
    selectedProject: undefined,
    refresh: () => {/**/},
    loading: defaultLoadingList,
});

// PROVIDER
interface RolesContextProviderProps {
    children: React.ReactNode;
}

export function RolesContextProvider(props: RolesContextProviderProps): JSX.Element {
    const session = useSession();
    const [organization, setOrganization] = useState<OrganizationObject|undefined>();
    const [users, setUsers] = useState<UserObject[]>([]);
    const [roles, setRoles] = useState<RoleObject[]>([]);
    const [accounts, setAccounts] = useState<AccountObject[]|undefined>();
    const [projects, setProjects] = useState<ProjectObject[]>([]);
    const [selectedProject, setSelectedProject] = useState<ProjectObject|undefined>();
    const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);

    // For demonstration purposes, we'll use mock data
    useEffect(() => {
        // Mock data setup
        setOrganization({
            id: "1",
            name: "Toshiba Organization",
            description: "Toshiba Admin Organization",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        });
        
        setUsers([
            {
                id: "1",
                organization_id: "1",
                firstname: "Admin",
                lastname: "User",
                email: "admin@example.com",
                is_superadmin: true,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        ]);
        
        setRoles([
            {
                id: "1",
                name: "Admin",
                permissions: {
                    "ACTION_CREATE": "Allow",
                    "ACTION_READ": "Allow",
                    "ACTION_UPDATE": "Allow",
                    "ACTION_DELETE": "Allow"
                },
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        ]);
        
        setAccounts([
            {
                id: "1",
                organization_id: "1",
                name: "Toshiba Account",
                description: "Main Toshiba Account",
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        ]);
        
        setProjects([
            {
                id: "1",
                account_id: "1",
                name: "Default Project",
                description: "Default Toshiba Project",
                datasets: [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        ]);
        
        setSelectedProject({
            id: "1",
            account_id: "1",
            name: "Default Project",
            description: "Default Toshiba Project",
            datasets: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        });
        
        // Set loading to false for all items
        setLoading({
            organization: false,
            accounts: false,
            projects: false,
            users: false,
            roles: false,
            addEditAccount: false,
            addEditProject: false,
            addEditUser: false,
            userProfile: {}
        });
    }, []);

    // FETCHING
    function refresh(refreshType: ACCESS_MANAGEMENT_TABS): void {
        // In a real implementation, this would refresh data from the backend
        console.log(`Refreshing ${refreshType} data`);
    }

    // MODIFYING
    async function actionAddAccount(accountName: string, accountDescription?: string): Promise<boolean> {
        console.log(`Adding account: ${accountName}, ${accountDescription}`);
        return true;
    }

    async function actionEditAccount(accountId: string, accountName: string, accountDescription?: string): Promise<boolean> {
        console.log(`Editing account: ${accountId}, ${accountName}, ${accountDescription}`);
        return true;
    }

    async function actionAddProject(accountId: string, projectName: string, projectDescription?: string, parentProjectId?: string): Promise<boolean> {
        console.log(`Adding project: ${accountId}, ${projectName}, ${projectDescription}, ${parentProjectId}`);
        return true;
    }

    async function actionEditProject(projectId: string, projectName: string, projectDescription?: string): Promise<boolean> {
        console.log(`Editing project: ${projectId}, ${projectName}, ${projectDescription}`);
        return true;
    }

    async function actionEditUser(userId: string, firstName: string, lastName: string): Promise<boolean> {
        console.log(`Editing user: ${userId}, ${firstName}, ${lastName}`);
        return true;
    }

    async function fetchUserProfile(userId: string): Promise<UserObject|undefined> {
        console.log(`Fetching user profile: ${userId}`);
        return users.find(user => user.id === userId);
    }

    // CONVENIENCE
    function updateState<ObjectType extends {id: string|number}>(object: ObjectType, setState: React.Dispatch<React.SetStateAction<ObjectType[]>>): void {
        setState(current => {
            const index = current.findIndex(item => item.id === object.id);
            if (index >= 0) {
                const updatedArray = [...current];
                updatedArray[index] = object;
                return updatedArray;
            } 
            return current;          
        });
    }

    return(
        <RolesContext.Provider
            value={ {
                organization,
                users,
                editUser: actionEditUser,
                getUserProfile: fetchUserProfile,
                roles,
                accounts,
                addAccount: actionAddAccount,
                editAccount: actionEditAccount,
                projects,
                addProject: actionAddProject,
                editProject: actionEditProject,
                selectedProject,
                refresh,
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
