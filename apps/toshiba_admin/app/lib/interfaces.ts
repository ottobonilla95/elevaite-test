// RBAC related interfaces for Toshiba Admin

import type {
  CommonInputProps,
  CommonCheckboxProps,
} from "@repo/ui/components";

// ENUMS
////////////////

export enum ACCESS_MANAGEMENT_TABS {
  ACCOUNTS = "Accounts",
  PROJECTS = "Projects",
  USERS = "Users",
  ROLES = "Roles",
}

export enum ROLE_PERMISSIONS {
  ACTION_CREATE = "ACTION_CREATE",
  ACTION_READ = "ACTION_READ",
  ACTION_UPDATE = "ACTION_UPDATE",
  ACTION_DELETE = "ACTION_DELETE",
}

// SYSTEM INTERFACES
////////////////

export interface SortingObject<
  ObjectToBeSorted,
  SpecialHandlingFieldsEnum = undefined,
> {
  field?: keyof ObjectToBeSorted;
  isDesc?: boolean;
  specialHandling?: SpecialHandlingFieldsEnum;
}

// RBAC
////////////////

export interface OrganizationObject {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface UserObject {
  id: string;
  organization_id: string;
  firstname?: string;
  lastname?: string;
  email: string;
  is_superadmin: boolean;
  created_at: string;
  updated_at: string;
  is_account_admin?: boolean;
  roles?: UserRoleObject[];
  account_memberships?: UserAccountMembershipObject[];
}

export interface ExtendedUserObject extends UserObject {
  displayRoles?: {
    roleLabel: string; // Role name or "Admin"
    roleParent?: string; // Account name or Project Name
  }[];
}

export interface UserAccountMembershipObject {
  account_id: string;
  account_name: string;
  is_admin: boolean;
  roles: UserRoleObject[];
}

export interface UserRoleObject {
  id: string;
  name: string;
}

export interface AccountObject {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  is_disabled?: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExtendedAccountObject extends AccountObject {
  projectCount?: number;
}

export interface ProjectObject {
  id: string;
  account_id: string;
  name: string;
  description: string;
  creator?: string;
  parent_project_id?: string;
  is_disabled?: boolean;
  datasets: RbacDatasetObject[];
  created_at: string;
  updated_at: string;
}

export interface ExtendedProjectObject extends ProjectObject {
  accountName?: string;
  parentProjectName?: string;
}

export interface RoleObject {
  id: string;
  name: string;
  permissions: RolePermission;
  created_at: string;
  updated_at: string;
}

export interface RolePermission {
  [name: string]: "Allow" | "Deny" | RolePermission;
}

export interface RbacDatasetObject {
  id: string;
  projectId: string;
  description?: string;
  name: string;
  versions: {
    id: string;
    commitId: string;
    version: string | number;
    createDate: string;
  }[];
  tags: {
    id: string;
    name: string;
  }[];
  createDate: string;
  updateDate?: string;
}

// Loading interface for RolesContext
export interface LoadingListObject {
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
