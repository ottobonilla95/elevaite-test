"use client";
import type { SVGProps, JSX } from "react";
import { useState } from "react";
import Image from "next/image";
import type { StaticImport } from "next/dist/shared/lib/get-img-props";
import { uploadToServer } from "../../lib/actions";
import ExcelSVG from "../icons/vscode-icons_file-type-excel.svg";
import type { UploadedFile } from "../../lib/interfaces";
import { UploadWidget } from "./UploadWidget";

interface UploadExcelProps {
  onSubmit: (_serverFiles: UploadedFile[], _files: File[]) => Promise<void>;
}

function UploadExcel({ onSubmit }: UploadExcelProps): JSX.Element {
  const [serverFiles, setServerFiles] = useState<UploadedFile[]>([]);
  const [originalFiles, setOriginalFiles] = useState<File[]>([]);
  // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars -- To be developed
  const [manifest, setManifest] = useState(false);
  // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars -- To be developed
  const [isLoading, setIsLoading] = useState(false);

  const handleCanclebutton = (): void => {
    setServerFiles([]);
    setOriginalFiles([]);
  };

  const handleFileSelect = async (acceptedFiles: File[]): Promise<void> => {
    const file = acceptedFiles[0];
    setIsLoading(true);
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Things might happen
    if (file) {
      const formData = new FormData();
      formData.append("file", file, encodeURIComponent(file.name));
      try {
        const data = await uploadToServer(formData);
        if (data.response === "Success") {
          serverFiles.push({
            fileSize: data.file_size,
            key: data.file_name,
            name: data.file_name,
            sheetCount: data.sheets_count,
            filePath: data.file_path,
            fileType: data.file_type,
            sheets: data.sheet,
          });
          originalFiles.push(file);
          setIsLoading(false);
        }
      } catch (error) {
        // eslint-disable-next-line no-console -- Implement better logging
        console.error("Error uploading file:", error);
      }
    }
  };

  const handleSubmitbutton = async (): Promise<void> => {
    await onSubmit(serverFiles, originalFiles);
  };
  return (
    <div className="flex flex-col w-3/5 h-full gap-5 pt-12 pb-12 justify-center">
      <UploadWidget handleFileSelect={handleFileSelect} />
      <div className="cards w-full flex flex-col gap-3 h-[calc(100vh-683px)] overflow-auto">
        {serverFiles.map((file) => (
          <FileCard
            file={file}
            key={file.key}
            onXClose={(key) => {
              setServerFiles(serverFiles.filter((_file) => _file.key !== key));
            }}
          />
        ))}
      </div>
      <div className="buttons flex flex-row justify-end w-full items-end gap-3">
        <button
          className="cancel flex justify-center items-center py-2.5 px-4 rounded-lg border border-solid border-[#D0D5DD] bg-white shadow-sm font-semibold text-sm"
          onClick={handleCanclebutton}
          type="button"
        >
          Cancel
        </button>
        <div className="submit flex justify-center items-center py-2.5 px-4 rounded-lg border border-solid border-[#F46F22] bg-[#F46F22] shadow-sm font-semibold text-sm text-white">
          <button onClick={handleSubmitbutton} type="button">
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}

export default UploadExcel;

interface FileCardProps {
  file: UploadedFile;
  onXClose: (key: string) => void;
}

function FileCard({ file, onXClose }: FileCardProps): JSX.Element {
  return (
    <div className="flex flex-col w-full p-3 gap-3 justify-center items-start rounded-lg bg-[#F8FAFB]">
      <div className="flex flex-col gap-2 self-stretch">
        <div className="flex flex-1 items-center gap-2">
          <Image alt="Excel Icon" height={24} src={ExcelSVG as StaticImport} width={24} />
          <span className="flex-grow text-sm font-medium">{file.name}</span>
          <XClose
            className="close cursor-pointer"
            onClick={() => {
              onXClose(file.key);
            }}
          />
        </div>
        <line className="w-full h-px bg-[#ECEFF3]" />
        <div className="flex justify-between items-center self-stretch">
          <span className="text-[#666D80] font-medium text-xs">
            {file.sheetCount}
            {" Sheets Found"}
          </span>
          <span className="text-[#121212] font-medium text-xs">
            <span className="text-[#666D80] font-medium text-xs">{"Size: "}</span>
            {file.fileSize}
          </span>
        </div>
      </div>
    </div>
  );
}

function XClose(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="m12 4-8 8m0-8 8 8" stroke="#666D80" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.333} />
    </svg>
  );
}
