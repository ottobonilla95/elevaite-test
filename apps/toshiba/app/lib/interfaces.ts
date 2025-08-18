// RBAC related interfaces for Toshiba Admin

import type {
  CommonInputProps,
  CommonCheckboxProps,
} from "@repo/ui/components";
import { v4 as uuidv4 } from "uuid";

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
  application_admin?: boolean;
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

// Enums, Interfaces, Types, and initializer objects
////////////////////////////////////////////////////

export const SESSION_ID_PREFIX = "sessionId_";
export const USER_MESSAGE_ID_PREFIX = "userMessageId_";
export const CHATBOT_MESSAGE_ID_PREFIX = "chatbotMessageId_";

export enum WindowGrid {
  active = "active-case",
  closed = "closed-case",
  dashboard = "dashboard",
  discover = "discover",
  toshiba1 = "toshiba1",
  toshiba2 = "toshiba2",
}

export enum ChatbotV {
  InWarranty = "in-warranty",
  OutOfWarranty = "out-of-warranty",
  AgentAssist = "agent-assist",
  Upsell = "upsell",
}
export const defaultChatbotV = ChatbotV.InWarranty;

export enum ChatBotGenAI {
  Pan = "pan",
  Cisco = "cisco",
  CiscoClo = "cisco_clo",
  ServiceNow = "servicenow",
  BGPInsights = "bgpinsights",
  ALSwitchLogs = "alswitchlogs",
}
export const defaultGenAIBotOption = ChatBotGenAI.CiscoClo;

export interface SessionObject {
  id: string;
  label: string;
  messages: ChatMessageObject[];
  creationDate: string;
  summary?: SessionSummaryObject;
  srNumber?: string;
}

export interface SessionSummaryObject {
  title: string;
  problem: string;
  solution: string;
  sessionMessageLengthOnLastUpdate?: number;
  isExpectingDisplay?: boolean;
}

export const defaultSession: SessionObject = {
  id: uuidv4().toString(),
  label: "Starting New Chat...",
  messages: [],
  creationDate: new Date().toISOString(),
};

export interface ChatMessageResponse {
  text: string;
  refs: string[];
  media?: string[];
}

export interface SourceReference {
  filename: string;
  pages: string;
  url?: string;
  awsLink?: string;
  fullMatchText?: string;
}

export interface ChatMessageObject {
  id: string;
  userName: string;
  isBot: boolean;
  date: string;
  text: string;
  vote?: 0 | 1 | -1;
  feedback?: string;
  feedbackfiles?: ChatMessageFileObject[];
  files?: ChatMessageFileObject[];
  media?: ChatMessageFileObject[];
  isStreaming?: boolean;
  agentStatus?: string;
  sources?: SourceReference[];
}

export interface ChatMessageFileObject {
  id: string;
  filename: string;
  fileType?: ChatMessageFileTypes;
  isDownloadable?: boolean;
  isViewable?: boolean;
}

export enum ChatMessageFileTypes {
  DOC = "document",
}
