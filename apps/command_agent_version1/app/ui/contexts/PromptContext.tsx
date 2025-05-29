"use client";
import { createContext, SetStateAction, useContext, useEffect, useState } from "react";
import { deploy, nextPage, previousPage, reRun, run, uploadFile } from "../../lib/actionsPrompt";
import { PageChangeResponseObject, PromptInputItem, PromptInputTypes, regenerateResponseObject, type UploadFileResponseObject } from "../../lib/interfaces";
import { toast } from "react-toastify";


// ENUMS and INTERFACES

export enum LoadingKeys {
  Uploading = "uploading",
  ChangingPage = "changingPage",
  Running = "running",
  Deploying = "deploying",
  Resetting = "resetting",
}


// STATICS

const defaultPageValue: number | null = null;
const defaultPromptInputs: PromptInputItem[] = Object.values(PromptInputTypes).map((type) => ({
  id: crypto.randomUUID().toString(),
  type: type as PromptInputTypes,
  prompt: "",
}));


// STRUCTURE

export interface PromptContextStructure {
  currentPage: number | null;
  setCurrentPage: (current: number | null) => void,
  goToNextPage: (useYolo: boolean) => Promise<PageChangeResponseObject | null>;
  goToPrevPage: (useYolo: boolean) => Promise<PageChangeResponseObject | null>;
  run: () => Promise<void>;
  deploy: () => Promise<void>;
  output: regenerateResponseObject|null;
  loading: Record<string, boolean>;
  fileUpload: (useYolo: boolean, file: File, isImage?: boolean) => Promise<UploadFileResponseObject | null>;
  showFileUploadModal: boolean,
  setShowFileUploadModal: (show: boolean) => void;
  invoiceImage: String | null;
  setInvoiceImage: (image: String | null) => void;
  invoiceNumPages: number | null,
  setInvoiceNumPages: (totalPages: number) => void,
  file: File | null;
  setFile: (file: File | null) => void;
  testingConsoleActiveClass: String,
  setTestingConsoleActiveClass: (activeClass: String) => void;
  // Add any additional properties or methods needed for the prompt context
  promptInputs: PromptInputItem[];
  addPromptInput: () => void;
  updatePromptInput: (id: string, changes: Partial<PromptInputItem>) => void;
  removePromptInput: (id: string) => void;
}

export const PromptContext = createContext<PromptContextStructure>({
  currentPage: defaultPageValue,
  setCurrentPage: () => undefined,
  goToNextPage: async () => null,
  goToPrevPage: async () => null,
  run: async () => undefined,
  deploy: async () => undefined,
  output: null,
  loading: {},
  fileUpload: async () => null,
  showFileUploadModal: false,
  setShowFileUploadModal: () => undefined,
  invoiceImage: null,
  setInvoiceImage: () => undefined,
  invoiceNumPages: null,
  setInvoiceNumPages: () => undefined,
  file: null,
  setFile: () => undefined,
  testingConsoleActiveClass: '',
  setTestingConsoleActiveClass: () => undefined,
  promptInputs: [],
  addPromptInput: () => undefined,
  updatePromptInput: () => undefined,
  removePromptInput: () => undefined,
});


// PROVIDER

interface PromptContextProviderProps {
  children: React.ReactNode;
}

export function PromptContextProvider(props: PromptContextProviderProps): React.ReactElement {
  const [sessionId, setSessionId] = useState("");
  const [currentPage, setCurrentPage] = useState<number | null>(defaultPageValue);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [showFileUploadModal, setShowFileUploadModal] = useState<boolean>(false);
  const [invoiceImage, setInvoiceImage] = useState<String | null>(null);
  const [invoiceNumPages, setInvoiceNumPages] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [testingConsoleActiveClass, setTestingConsoleActiveClass] = useState<String>('');
  const [promptInputs, setPromptInputs] = useState<PromptInputItem[]>(defaultPromptInputs);
  const [output, setOutput] = useState<regenerateResponseObject|null>(null);
  

  useEffect(() => {
    setSessionId(`sid-${crypto.randomUUID().toString()}`);
  }, []);


  function addPromptInput(): void {
    const newPromptInput = {
      id: crypto.randomUUID().toString(),
      type: PromptInputTypes.UserInstructions,
      prompt: "",
    }
    setPromptInputs(current => {
      return [newPromptInput, ...current];
    });
  }

  function updatePromptInput(id: string, changes: Partial<PromptInputItem>): void {
    setPromptInputs((current) =>
      current.map((input) => (input.id === id ? { ...input, ...changes } : input))
    );
  }

  function removePromptInput(id: string): void {
    setPromptInputs((current) => current.filter((input) => input.id !== id));
  }


  function getPromptInputsOptions(): {
    userFeedback?: string;
    tableHeader?: string;
    lineItems?: string;
    expectedOutput?: string;
  }|undefined {
    if (!promptInputs || promptInputs.length === 0) return;

    const options: {
      userFeedback?: string;
      tableHeader?: string;
      lineItems?: string;
      expectedOutput?: string;
    } = {};

    for (var input of promptInputs) {
      switch (input.type) {
        case PromptInputTypes.UserInstructions:
          options.userFeedback = options.userFeedback ? options.userFeedback + "\n" + input.prompt : input.prompt;
          break;
        case PromptInputTypes.TableHeader:
          options.tableHeader = options.tableHeader ? options.tableHeader + "\n" + input.prompt : input.prompt;
          break;
        case PromptInputTypes.LineItems:
          options.lineItems = options.lineItems ? options.lineItems + "\n" + input.prompt : input.prompt;
          break;
        case PromptInputTypes.ExpectedOutput:
          options.expectedOutput = options.expectedOutput ? options.expectedOutput + "\n" + input.prompt : input.prompt;
          break;
      }
    }

    return options;
  }



  function setLoadingState(key: LoadingKeys, value: boolean): void {
    setLoading((prev) => ({ ...prev, [key]: value }));
  }




  // Server Actions

  async function actionFileUpload(useYolo: boolean, file: File, isImage = false): Promise<UploadFileResponseObject | null> {
    setLoadingState(LoadingKeys.Uploading, true);
    try {
      const result = await uploadFile(sessionId, useYolo, file, isImage);
      if (result) setOutput(null);
      return result;
    } catch (error) {
      // eslint-disable-next-line no-console -- placeholder for error logging
      console.error("File upload failed:", error);
      return null;
    } finally {
      setLoadingState(LoadingKeys.Uploading, false);
    }
  }

  async function goToNextPage(useYolo: boolean): Promise<PageChangeResponseObject | null> {
    setLoadingState(LoadingKeys.ChangingPage, true);
    try {
      const result = await nextPage(sessionId, useYolo);
	    setCurrentPage((current) => (current === null ? 1 : current + 1));
      return result;
    } catch (error) {
      // eslint-disable-next-line no-console -- placeholder for error logging
      console.error("Going to the next page failed:", error);
      return null;
    } finally {
      setLoadingState(LoadingKeys.ChangingPage, false);
    }
  }

  async function goToPrevPage(useYolo: boolean): Promise<PageChangeResponseObject | null> {
    setLoadingState(LoadingKeys.ChangingPage, true);
    try {
      const result = await previousPage(sessionId, useYolo);
	    setCurrentPage((current) => {
      if (current === null || current <= 1) return 1;
      	return current - 1;
      });
      return result;
    } catch (error) {
      // eslint-disable-next-line no-console -- placeholder for error logging
      console.error("Going to the previous page failed:", error);
      return null;
    } finally {
      setLoadingState(LoadingKeys.ChangingPage, false);
    }
  }

  async function actionRun(): Promise<void> {
    setLoadingState(LoadingKeys.Running, true);
    try {
      const result = await reRun(sessionId, getPromptInputsOptions());
      console.log("RE Run result", result);
      setOutput(result);
    } catch (error) {
      console.error("Run action failed:", error);
    } finally {
      setLoadingState(LoadingKeys.Running, false);
    }
  }

  async function actionDeploy(originalText?: string, extractionPrompt?: string): Promise<void> {
    setLoadingState(LoadingKeys.Deploying, true);
    try {
      await deploy(sessionId, originalText ?? "", extractionPrompt ?? "");      
      toast.success(
        <div className="prompt-toast rounded-md font-bold text-sm flex items-center justify-between w-full">
          Data deployed successfully.
        </div>,
        { position: 'bottom-right', }
      )
    } catch (error) {
      console.error("Deploy action failed:", error);
    } finally {
    setLoadingState(LoadingKeys.Deploying, false);
    }
  }





  return (
    <PromptContext.Provider
      value={{
        currentPage,
		    setCurrentPage,
        goToNextPage,
        goToPrevPage,
        run: actionRun,
        deploy: actionDeploy,
        output,
        loading,
        fileUpload: actionFileUpload,
        showFileUploadModal, // Placeholder for file upload modal state
        setShowFileUploadModal,
        invoiceImage,
        setInvoiceImage,
        invoiceNumPages,
        setInvoiceNumPages,
        file,
        setFile,
        testingConsoleActiveClass,
        setTestingConsoleActiveClass,
        promptInputs,
        addPromptInput,
        updatePromptInput,
        removePromptInput,
      }}
    >
      {props.children}
    </PromptContext.Provider>
  );
}

export function usePrompt(): PromptContextStructure {
  return useContext(PromptContext);
}
