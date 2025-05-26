"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { uploadFile } from "../../lib/actionsPrompt";
import type { UploadFileResponse } from "../../lib/interfaces";


// ENUMS and INTERFACES

// (Add any enums or interfaces for prompt settings if needed)


// STATICS

const defaultPageValue: number | null = null;


// STRUCTURE

export interface PromptContextStructure {
  currentPage: number | null;
  goToNextPage: () => void;
  goToPrevPage: () => void;
  isFileUploading: boolean;
  handleFileUpload: (sessionId: string, useYolo: boolean, file: File, isImage?: boolean) => Promise<UploadFileResponse | null>;
}

export const PromptContext = createContext<PromptContextStructure>({
  currentPage: defaultPageValue,
  goToNextPage: () => { /** */ },
  goToPrevPage: () => { /** */ },
  isFileUploading: false,
  handleFileUpload: async () => null,
});


// PROVIDER

interface PromptContextProviderProps {
  children: React.ReactNode;
}

export function PromptContextProvider(props: PromptContextProviderProps): React.ReactElement {
  const [currentPage, setCurrentPage] = useState<number | null>(defaultPageValue);
  const [isFileUploading, setIsFileUploading] = useState<boolean>(false);


  useEffect(() => {    
    console.log("This is a test! Page was changed to:", currentPage);
  }, [currentPage]);


  function goToNextPage(): void {
    setCurrentPage((current) => (current === null ? 1 : current + 1));
  }

  function goToPrevPage(): void {
    setCurrentPage((current) => {
      if (current === null || current <= 1) return 1;
      return current - 1;
    });
  }


  // Actions

  async function handleFileUpload(sessionId: string, useYolo: boolean, file: File, isImage = false): Promise<UploadFileResponse | null> {    
    setIsFileUploading(true);
    try {
      const result = await uploadFile(sessionId, useYolo, file, isImage);
      return result;
    } catch (error) {
      // eslint-disable-next-line no-console -- placeholder for error logging
      console.error("File upload failed:", error);
      return null;
    } finally {
      setIsFileUploading(false);
    }
  }



  return (
    <PromptContext.Provider
      value={{
        currentPage,
        goToNextPage,
        goToPrevPage,
        isFileUploading,
        handleFileUpload,
      }}
    >
      {props.children}
    </PromptContext.Provider>
  );
}

export function usePrompt(): PromptContextStructure {
  return useContext(PromptContext);
}
