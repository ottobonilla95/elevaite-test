import type { WorkflowConfig } from "../model/workflowSteps";

export interface DraftWorkflowState {
  workflow?: WorkflowConfig;
  isDirty: boolean;
}

export const initialDraftWorkflowState: DraftWorkflowState = {
  workflow: undefined,
  isDirty: false,
};
