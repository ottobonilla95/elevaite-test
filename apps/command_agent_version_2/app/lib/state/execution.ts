import type { ExecutionStatusResponse } from "../model/workflowSteps";

export interface ExecutionStateSlice {
  current?: ExecutionStatusResponse;
  isPolling: boolean;
}

export const initialExecutionState: ExecutionStateSlice = {
  current: undefined,
  isPolling: false,
};
