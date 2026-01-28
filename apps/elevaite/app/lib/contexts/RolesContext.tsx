"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState } from "react";
import {
  addAccount,
  addProject,
  editAccount,
  editProject,
  editUser,
  getAccounts,
  getOrganization,
  getOrganizationUsers,
  getProjects,
  getRoles,
  getUserProfile,
} from "../actions/rbacActions";
import {
  ACCESS_MANAGEMENT_TABS,
  type AccountObject,
  type OrganizationObject,
  type ProjectObject,
  type RoleObject,
  type UserObject,
} from "../interfaces";

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

// INTERFACES

interface LoadingListObject {
  organization: boolean;
  accounts: boolean;
  projects: boolean;
  users: boolean;
  roles: boolean;
  addEditAccount: boolean;
  addEditProject: boolean;
  addEditUser: boolean;
  userProfile: Record<string, boolean>;
}

// STRUCTURE

function simpleAsyncBoolean(): Promise<boolean> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(false);
    }, 100);
  });
}

export interface RolesContextStructure {
  organization: OrganizationObject | undefined;
  users: UserObject[];
  editUser: (
    userId: string,
    firstName: string,
    lastName: string,
  ) => Promise<boolean>;
  getUserProfile: (userId: string) => Promise<UserObject | undefined>;
  roles: RoleObject[];
  accounts: AccountObject[] | undefined;
  addAccount: (
    accountName: string,
    accountDescription?: string,
  ) => Promise<boolean>;
  editAccount: (
    accountId: string,
    accountName: string,
    accountDescription?: string,
  ) => Promise<boolean>;
  addProject: (
    accountId: string,
    projectName: string,
    projectDescription?: string,
    parentProjectId?: string,
  ) => Promise<boolean>;
  editProject: (
    projectId: string,
    projectName: string,
    projectDescription?: string,
  ) => Promise<boolean>;
  projects: ProjectObject[];
  selectedProject: ProjectObject | undefined;
  refresh: (refreshType: ACCESS_MANAGEMENT_TABS) => void;
  loading: LoadingListObject;
}

export const RolesContext = createContext<RolesContextStructure>({
  organization: undefined,
  users: [],
  editUser: async () => {
    await simpleAsyncBoolean();
    return false;
  },
  getUserProfile: async () => {
    await simpleAsyncBoolean();
    return undefined;
  },
  roles: [],
  accounts: undefined,
  addAccount: async () => {
    await simpleAsyncBoolean();
    return false;
  },
  editAccount: async () => {
    await simpleAsyncBoolean();
    return false;
  },
  addProject: async () => {
    await simpleAsyncBoolean();
    return false;
  },
  editProject: async () => {
    await simpleAsyncBoolean();
    return false;
  },
  projects: [],
  selectedProject: undefined,
  refresh: () => {
    /**/
  },
  loading: defaultLoadingList,
});

// PROVIDER

interface RolesContextProviderProps {
  children: React.ReactNode;
}

export function RolesContextProvider(
  props: RolesContextProviderProps,
): JSX.Element {
  const session = useSession();
  const [organization, setOrganization] = useState<
    OrganizationObject | undefined
  >();
  const [users, setUsers] = useState<UserObject[]>([]);
  const [roles, setRoles] = useState<RoleObject[]>([]);
  const [accounts, setAccounts] = useState<AccountObject[] | undefined>();
  const [projects, setProjects] = useState<ProjectObject[]>([]);
  const [selectedProject, setSelectedProject] = useState<
    ProjectObject | undefined
  >();
  const [loading, setLoading] = useState<LoadingListObject>(defaultLoadingList);

  useEffect(() => {
    if (session.data?.authToken) {
      void fetchOrganization(session.data.authToken);
      void fetchOrganizationUsers(session.data.authToken);
      void fetchRoles(session.data.authToken);
      void fetchAccounts(session.data.authToken);
    }
  }, []);

  useEffect(() => {
    if (session.data?.authToken && accounts) {
      void fetchAllProjects(accounts, session.data.authToken);
    }
  }, [accounts]);

  useEffect(() => {
    if (projects.length > 0) {
      const defaultProject = projects.find(
        (project) => project.name.toLowerCase() === "default project",
      );
      if (defaultProject) {
        setSelectedProject(defaultProject);
      }
    }
  }, [projects]);

  // FETCHING
  /////////////////

  function refresh(refreshType: ACCESS_MANAGEMENT_TABS): void {
    if (!session.data?.authToken) return;
    switch (refreshType) {
      case ACCESS_MANAGEMENT_TABS.ACCOUNTS:
        void fetchAccounts(session.data.authToken, true);
        break;
      case ACCESS_MANAGEMENT_TABS.PROJECTS:
        void fetchAllProjects(accounts ?? [], session.data.authToken, true);
        break;
      case ACCESS_MANAGEMENT_TABS.USERS:
        void fetchOrganizationUsers(session.data.authToken, true);
        break;
      case ACCESS_MANAGEMENT_TABS.ROLES:
        void fetchRoles(session.data.authToken, true);
        break;
    }
  }

  async function fetchOrganization(authToken: string): Promise<void> {
    try {
      setLoading((current) => {
        return { ...current, organization: true };
      });
      const fetchedOrganization = await getOrganization(authToken);
      setOrganization(fetchedOrganization);
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching organization:", error);
    } finally {
      setLoading((current) => {
        return { ...current, organization: false };
      });
    }
  }

  async function fetchOrganizationUsers(
    authToken: string,
    forceRevalidation?: boolean,
  ): Promise<void> {
    try {
      setLoading((current) => {
        return { ...current, users: true };
      });
      const fetchedUsers = await getOrganizationUsers(
        authToken,
        forceRevalidation,
      );
      setUsers(fetchedUsers);
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching users of organization:", error);
    } finally {
      setLoading((current) => {
        return { ...current, users: false };
      });
    }
  }

  async function fetchUserProfile(
    userId: string,
  ): Promise<UserObject | undefined> {
    if (!session.data?.authToken) return;
    try {
      setLoading((current) => ({
        ...current,
        userProfile: { ...current.userProfile, [userId]: true },
      }));
      const fetchedUser = await getUserProfile(session.data.authToken, userId);
      return fetchedUser;
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching user profile:", error);
    } finally {
      setLoading((current) => ({
        ...current,
        userProfile: { ...current.userProfile, [userId]: false },
      }));
    }
  }

  async function fetchRoles(
    authToken: string,
    forceRevalidation?: boolean,
  ): Promise<void> {
    try {
      setLoading((current) => {
        return { ...current, roles: true };
      });
      const fetchedRoles = await getRoles(authToken, forceRevalidation);
      setRoles(fetchedRoles);
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching roles:", error);
    } finally {
      setLoading((current) => {
        return { ...current, roles: false };
      });
    }
  }

  async function fetchAccounts(
    authToken: string,
    forceRevalidation?: boolean,
  ): Promise<void> {
    try {
      setLoading((current) => {
        return { ...current, accounts: true };
      });
      const fetchedAccounts = await getAccounts(authToken, forceRevalidation);
      setAccounts(fetchedAccounts);
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching accounts:", error);
    } finally {
      setLoading((current) => {
        return { ...current, accounts: false };
      });
    }
  }

  async function fetchProjects(
    accountId: string,
    authToken: string,
    forceRevalidation?: boolean,
  ): Promise<ProjectObject[] | undefined> {
    try {
      return await getProjects(accountId, authToken, forceRevalidation);
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching projects:", error);
    }
  }

  async function fetchAllProjects(
    passedAccounts: AccountObject[],
    authToken: string,
    forceRevalidation?: boolean,
  ): Promise<void> {
    setLoading((current) => {
      return { ...current, projects: true };
    });
    const projectPromises = passedAccounts.map((account) =>
      fetchProjects(account.id, authToken, forceRevalidation),
    );
    const results = await Promise.all(projectPromises);
    const allProjects = results
      .flat()
      .filter((p): p is ProjectObject => p !== null && p !== undefined);
    setProjects(allProjects);
    setLoading((current) => {
      return { ...current, projects: false };
    });
  }

  // MODIFYING
  /////////////////

  async function actionAddAccount(
    accountName: string,
    accountDescription?: string,
  ): Promise<boolean> {
    if (!session.data?.authToken || !organization) return false;
    try {
      setLoading((current) => {
        return { ...current, addEditAccount: true };
      });
      const result = await addAccount(
        session.data.authToken,
        organization.id,
        accountName,
        accountDescription ?? "",
      );
      updateState<AccountObject>(result, setAccounts);
      return true;
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in adding account:", error);
      return false;
    } finally {
      setLoading((current) => {
        return { ...current, addEditAccount: false };
      });
    }
  }

  async function actionEditAccount(
    accountId: string,
    accountName: string,
    accountDescription?: string,
  ): Promise<boolean> {
    if (!session.data?.authToken) return false;
    try {
      setLoading((current) => {
        return { ...current, addEditAccount: true };
      });
      const result = await editAccount(
        session.data.authToken,
        accountId,
        accountName,
        accountDescription ?? "",
      );
      updateState<AccountObject>(result, setAccounts);
      return true;
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in editing account:", error);
      return false;
    } finally {
      setLoading((current) => {
        return { ...current, addEditAccount: false };
      });
    }
  }

  async function actionAddProject(
    accountId: string,
    projectName: string,
    projectDescription?: string,
    parentProjectId?: string,
  ): Promise<boolean> {
    if (!session.data?.authToken) return false;
    try {
      setLoading((current) => {
        return { ...current, addEditProject: true };
      });
      const result = await addProject(
        session.data.authToken,
        accountId,
        projectName,
        projectDescription ?? "",
        parentProjectId,
      );
      updateState<ProjectObject>(result, setProjects);
      return true;
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in adding project:", error);
      return false;
    } finally {
      setLoading((current) => {
        return { ...current, addEditProject: false };
      });
    }
  }

  async function actionEditProject(
    projectId: string,
    projectName: string,
    projectDescription?: string,
  ): Promise<boolean> {
    if (!session.data?.authToken) return false;
    try {
      setLoading((current) => {
        return { ...current, addEditProject: true };
      });
      const result = await editProject(
        session.data.authToken,
        projectId,
        projectName,
        projectDescription ?? "",
      );
      updateState<ProjectObject>(result, setProjects);
      return true;
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in editing project:", error);
      return false;
    } finally {
      setLoading((current) => {
        return { ...current, addEditProject: false };
      });
    }
  }

  // Add User has issues

  async function actionEditUser(
    userId: string,
    firstName: string,
    lastName: string,
  ): Promise<boolean> {
    if (!session.data?.authToken) return false;
    try {
      setLoading((current) => {
        return { ...current, addEditUser: true };
      });
      const result = await editUser(
        session.data.authToken,
        userId,
        firstName,
        lastName,
      );
      updateState<UserObject>(result, setUsers);
      return true;
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in editing user:", error);
      return false;
    } finally {
      setLoading((current) => {
        return { ...current, addEditUser: false };
      });
    }
  }

  // CONVENIENCE
  /////////////////

  function updateState<ObjectType extends { id: string | number }>(
    object: ObjectType,
    setState: React.Dispatch<React.SetStateAction<ObjectType[]>>,
  ): void {
    setState((current) => {
      const index = current.findIndex((item) => item.id === object.id);
      if (index >= 0) {
        const updatedArray = [...current];
        updatedArray[index] = object;
        return updatedArray;
      }
      return current;
    });
  }

  return (
    <RolesContext.Provider
      value={{
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
      }}
    >
      {props.children}
    </RolesContext.Provider>
  );
}

export function useRoles(): RolesContextStructure {
  return useContext(RolesContext);
}
