"use client";
import { ChangeEvent, createContext, SetStateAction, useContext, useEffect, useState } from "react";
import { deploy, nextPage, previousPage, processCurrentPage, reRun, run, uploadFile } from "../../lib/actionsPrompt";
import { PageChangeResponseObject, ProcessCurrentPageResponseObject, PromptInputItem, PromptInputTypes, PromptInputVariableEngineerItem, regenerateResponseObject, type UploadFileResponseObject } from "../../lib/interfaces";
import { toast } from "react-toastify";
import { usePathname } from "next/navigation";


// ENUMS and INTERFACES

export enum LoadingKeys {
  Uploading = "uploading",
  ChangingPage = "changingPage",
  Running = "running",
  Deploying = "deploying",
  Resetting = "resetting",
  ConvertingToJSON = 'converting to json',
}


// STATICS

const defaultPageValue: number | null = null;
const defaultPromptInputs: PromptInputItem[] = Object.values(PromptInputTypes).slice(0, 3).map((type) => ({
  id: crypto.randomUUID().toString(),
  type: type as PromptInputTypes,
  prompt: "",
  values: []
}));


// STRUCTURE

export interface PromptContextStructure {
  currentPage: number | null;
  setCurrentPage: (current: number | null) => void,
  goToNextPage: (useYolo: boolean) => Promise<PageChangeResponseObject | null>;
  goToPrevPage: (useYolo: boolean) => Promise<PageChangeResponseObject | null>;
  run: () => Promise<void>;
  deploy: () => Promise<void>;
  output: regenerateResponseObject | null;
  setOutput: (response: regenerateResponseObject | null) => void
  loading: Record<string, boolean>;
  fileUpload: (useYolo: boolean, file: File, isImage?: boolean) => Promise<UploadFileResponseObject | null>;
  processCurrentPage: () => Promise<ProcessCurrentPageResponseObject | null>;
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
  setPromptInputs: (promptInputs: PromptInputItem[]) => void;
  addPromptInput: () => void;
  updatePromptInput: (id: string, changes: Partial<PromptInputItem>) => void;
  removePromptInput: (id: string) => void;
  isRightColExpanded: boolean,
  setIsRightColExpanded: (isExpanded: boolean) => void,
  isRightColPromptInputsColExpanded: boolean,
  setIsRightColPromptInputsColExpanded: (isExpanded: boolean) => void,
  isRightColOutputColExpanded: boolean,
  setIsRightColOutputColExpanded: (isExpanded: boolean) => void,
  outputVersions: regenerateResponseObject[];
  setOutputVersions: React.Dispatch<React.SetStateAction<regenerateResponseObject[]>>;
  handleReset: () => void,
  turnToJSON: (e: ChangeEvent<HTMLInputElement>) => Promise<void>;
  jsonOutput: String,
  setJsonOutput: (output: string) => void,
  defaultPromptInputs: PromptInputItem[],
  actionRunOnSelectedPages: (pages: number[]) => void,
  isEngineerPage: boolean,
  promptInputVariablesEngineer: PromptInputVariableEngineerItem[],
  setPromptInputVariablesEngineer: (variables: PromptInputVariableEngineerItem[]) => void,
  addPromptInputVariableEngineer: () => void,
  savePromptInputVariableEngineer: (id: string, updates: PromptInputVariableEngineerItem) => void,
  editPromptInputVariableEngineer: (id: string) => void,
  removePromptInputVariableEngineer: (id: string) => void
}

export const PromptContext = createContext<PromptContextStructure>({
  currentPage: defaultPageValue,
  setCurrentPage: () => undefined,
  goToNextPage: async () => null,
  goToPrevPage: async () => null,
  run: async () => undefined,
  deploy: async () => undefined,
  output: null,
  setOutput: () => undefined,
  loading: {},
  fileUpload: async () => null,
  processCurrentPage: async () => null,
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
  setPromptInputs: () => undefined,
  addPromptInput: () => undefined,
  updatePromptInput: () => undefined,
  removePromptInput: () => undefined,
  isRightColExpanded: true,
  isRightColPromptInputsColExpanded: false,
  setIsRightColPromptInputsColExpanded: () => undefined,
  isRightColOutputColExpanded: false,
  setIsRightColOutputColExpanded: () => undefined,
  setIsRightColExpanded: () => undefined,
  outputVersions: [],
  setOutputVersions: () => undefined,
  handleReset: () => undefined,
  turnToJSON: async () => { },
  jsonOutput: '',
  setJsonOutput: () => undefined,
  defaultPromptInputs: [],
  actionRunOnSelectedPages: () => undefined,
  isEngineerPage: false,
  promptInputVariablesEngineer: [],
  setPromptInputVariablesEngineer: () => undefined,
  addPromptInputVariableEngineer: () => undefined,
  savePromptInputVariableEngineer: () => undefined,
  editPromptInputVariableEngineer: () => undefined,
  removePromptInputVariableEngineer: () => undefined,
});


// PROVIDER

interface PromptContextProviderProps {
  children: React.ReactNode;
}

export function PromptContextProvider(props: PromptContextProviderProps): React.ReactElement {
  // check if it's the engineer page
  const pathname = usePathname();
  const isEngineerPage = pathname === '/prompt-engineer';

  const [sessionId, setSessionId] = useState("");
  const [currentPage, setCurrentPage] = useState<number | null>(defaultPageValue);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [showFileUploadModal, setShowFileUploadModal] = useState<boolean>(false);
  const [invoiceImage, setInvoiceImage] = useState<String | null>(null);
  const [invoiceNumPages, setInvoiceNumPages] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [testingConsoleActiveClass, setTestingConsoleActiveClass] = useState<String>('');
  const [promptInputs, setPromptInputs] = useState<PromptInputItem[]>(defaultPromptInputs);
  const [output, setOutput] = useState<regenerateResponseObject | null>(null);
  const [isRightColExpanded, setIsRightColExpanded] = useState<boolean>(!isEngineerPage);
  const [isRightColPromptInputsColExpanded, setIsRightColPromptInputsColExpanded] = useState<boolean>(false);
  const [isRightColOutputColExpanded, setIsRightColOutputColExpanded] = useState<boolean>(false);
  const [outputVersions, setOutputVersions] = useState<regenerateResponseObject[]>([]);
  const [jsonOutput, setJsonOutput] = useState('');
  const [promptInputVariablesEngineer, setPromptInputVariablesEngineer] = useState<PromptInputVariableEngineerItem[]>([]);

  useEffect(() => {
    setSessionId(`sid-${crypto.randomUUID().toString()}`);
  }, []);

  function addPromptInputVariableEngineer() {
	const newVariable: PromptInputVariableEngineerItem = {
		id: crypto.randomUUID().toString(),
		name: "",
		displayName: "",
		type: "Text",
		required: true,
		json: true,
		definition: "",
	}

	setPromptInputVariablesEngineer(current => {
      return [newVariable, ...current];
    });
  }

  useEffect(() => {
	console.log("Prompt Input Variables Engineer", promptInputVariablesEngineer);
  }, [promptInputVariablesEngineer]);

  function savePromptInputVariableEngineer(id: string, updates: PromptInputVariableEngineerItem ) {
	setPromptInputVariablesEngineer((current) =>
      current.map(input => (input.id === id ? { ...input, ...updates } : input))
    );
  }

  function editPromptInputVariableEngineer(id: string) {
	setPromptInputVariablesEngineer((current) =>
      current.map(input => (input.id === id ? { ...input, saved: false } : input))
    );
  }

  function removePromptInputVariableEngineer(id: string) {
	setPromptInputVariablesEngineer(current => current.filter(input => input.id !== id))
  }

  function addPromptInput(): void {
    const newPromptInput = {
      id: crypto.randomUUID().toString(),
      type: PromptInputTypes.DocumentHeader,
      prompt: "",
      values: []
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
    documentHeader?: string,
    lineItemHeader?: string;
    userFeedback?: string;
    lineItems?: string;
    expectedOutput?: string;
  } | undefined {
    if (!promptInputs || promptInputs.length === 0) return;

    const options: {
      documentHeader?: string,
      lineItemHeader?: string;
      userFeedback?: string;
      lineItems?: string;
      expectedOutput?: string;
    } = {};

    for (var input of promptInputs) {
      switch (input.type) {
        case PromptInputTypes.DocumentHeader:
          const joinedDocumentHeaderValues = Array.isArray(input.values) ? input.values.join(",") : input.values;
          options.documentHeader = options.documentHeader ? options.documentHeader + "," + joinedDocumentHeaderValues : joinedDocumentHeaderValues;
          break;
        case PromptInputTypes.LineItemHeader:
          const joinedLineItemHeaderValues = Array.isArray(input.values) ? input.values.join(",") : input.values;
          options.lineItemHeader = options.lineItemHeader ? options.lineItemHeader + "," + joinedLineItemHeaderValues : joinedLineItemHeaderValues;
          break;
        case PromptInputTypes.UserFeedback:
          options.userFeedback = options.userFeedback ? options.userFeedback + "\n" + input.prompt : input.prompt;
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


  function handleReset() {
    setLoadingState(LoadingKeys.Resetting, true);
    setTimeout(function () {
      setInvoiceNumPages(null);
      setFile(null);
      setInvoiceImage(null);
      setOutput(null);
      setOutputVersions([]);
      setJsonOutput('');
      setPromptInputs(
        defaultPromptInputs.map(input => ({
          ...input,
          prompt: "",
          //id: crypto.randomUUID().toString(),
        }))
      );
      setLoadingState(LoadingKeys.Resetting, false);
    }, 500);
  }


  // Server Actions

  async function actionFileUpload(useYolo: boolean, file: File, isImage = false): Promise<UploadFileResponseObject | null> {
    setLoadingState(LoadingKeys.Uploading, true);

    if (output?.response) {
      setOutput(null);
      setOutputVersions([]);
      setJsonOutput('');
      setPromptInputs(
        defaultPromptInputs.map(input => ({
          ...input,
          prompt: "",
          //id: crypto.randomUUID().toString(),
        }))
      );
    }

    try {
      const result = await uploadFile(sessionId, useYolo, file, isImage);
      if (result) setOutput(null);
      return result;
    } catch (error) {
      // eslint-disable-next-line no-console -- placeholder for error logging
      console.error("File upload failed:", error);
      return null;
    } finally {
      //setLoadingState(LoadingKeys.Uploading, false);
    }
  }

  async function actionProcessCurrentPage(): Promise<ProcessCurrentPageResponseObject | null> {
    //setLoadingState(LoadingKeys.Uploading, true);

    if (output?.result) {
      setOutput(null);
      setOutputVersions([]);
      setJsonOutput('');
      setPromptInputs(
        defaultPromptInputs.map(input => ({
          ...input,
          prompt: "",
          values: []
        }))
      );
    }

    try {
      const result = await processCurrentPage(sessionId);
      if (result) setOutput(null);
      return result;
    } catch (error) {
      // eslint-disable-next-line no-console -- placeholder for error logging
      console.error("Process current page failed:", error);
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
    console.log(getPromptInputsOptions())
    try {
      const result = await reRun(sessionId, getPromptInputsOptions());
      console.log("RE Run result", result);
      setOutput(result);
      setOutputVersions((prev) => [
        ...prev,
        {
          id: `genprompt_${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`,
          //active: false,
          ...result
        }
      ]);

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

  /* **Output:**
  <|dict|>{
    'Period of Account': '01/08/24 - 31/08/24',
    'Previous Balance': '0.0000 €',
    'Fixed Charges': '48,2200 €',
    'Additional Charges': '8,7243 €',
    'Discounts': '-21,8400 €',
    'Total of Current Account (without VAT)': '35,1043 €',
    'End of Mobile Subscription Fee': '3,5104 €',
    'Total VAT': '9,2675 €',
    'Total of Current Account (with VAT)': '47,8822 €',
    'Amount to be Paid (with VAT)': '47.88 €'
  }<|end_dict|> */
  async function turnToJSON(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.checked) {
      setLoadingState(LoadingKeys.ConvertingToJSON, true);
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_OPENROUTER_BASE_ENDPOINT}`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${process.env.NEXT_PUBLIC_OPENROUTER_API_KEY}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            "model": `${process.env.NEXT_PUBLIC_OPENROUTER_AI_MODEL}`,
            'response_format': {
              'type': 'json_object'
            },
            "messages": [
              {
                "role": "user",
                "content": `turn this to json
						${output?.result}
					`
              }
            ]
          })
        });
        const data = await response.json();
        setJsonOutput(data?.choices[0]?.message?.content);
      } catch (error) {
        console.error("Error turning the output to JSON:", error);
      } finally {
        setLoadingState(LoadingKeys.ConvertingToJSON, false);
      }
    } else {
      setJsonOutput('');
    }
  }

  function actionRunOnSelectedPages(pages: number[]) {
    console.log("run action for pages " + pages.join(','));
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
        setOutput,
        loading,
        fileUpload: actionFileUpload,
        processCurrentPage: actionProcessCurrentPage,
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
        setPromptInputs,
        addPromptInput,
        updatePromptInput,
        removePromptInput,
        isRightColExpanded,
        setIsRightColExpanded,
        isRightColPromptInputsColExpanded,
        setIsRightColPromptInputsColExpanded,
        isRightColOutputColExpanded,
        setIsRightColOutputColExpanded,
        outputVersions,
        setOutputVersions,
        handleReset,
        turnToJSON,
        jsonOutput,
        setJsonOutput,
        defaultPromptInputs,
        actionRunOnSelectedPages,
		isEngineerPage,
		promptInputVariablesEngineer,
		setPromptInputVariablesEngineer,
		addPromptInputVariableEngineer,
		savePromptInputVariableEngineer,
		editPromptInputVariableEngineer,
		removePromptInputVariableEngineer
      }}
    >
      {props.children}
    </PromptContext.Provider>
  );
}

export function usePrompt(): PromptContextStructure {
  return useContext(PromptContext);
}
