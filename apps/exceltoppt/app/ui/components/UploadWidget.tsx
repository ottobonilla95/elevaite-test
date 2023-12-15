"use client";
import { useRef } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud02 } from "../icons";

interface UploadWidgetProps {
  handleFileSelect: (acceptedFiles: File[]) => Promise<void>;
}

function UploadWidget({ handleFileSelect }: UploadWidgetProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { getRootProps, getInputProps } = useDropzone({
    onDrop: (acceptedFiles) => handleFileSelect(acceptedFiles),
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.ms-excel.sheet.macroEnabled.12": [".xlsm"],
    },
  });

  const handleFileInputChange = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  return (
    <div
      className="upload-widget flex flex-col items-center justify-center bg-black rounded-md gap-4 h-[250px] cursor-pointer"
      {...getRootProps()}
    >
      <input type="file" accept=".xlsx" {...getInputProps()} />
      <div className="upload-icon m-px rounded-full bg-[#F6F8FA] p-3">
        <UploadCloud02 className="upload-cloud-icon text-[#666D80] " onClick={() => {}} />
      </div>
      <div className="flex flex-col items-center">
        <p className="upload-text text-[#D9F27E] hover:text-[#6941C6]  transition-colors">Click to upload Excel File</p>
        <p className="upload-sub-text text-sm text-white">or drag and drop your .xlsx file</p>
      </div>
    </div>
  );
}

export default UploadWidget;
