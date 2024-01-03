import React from "react";
import type { JSX } from "react";
import { UploadWidget } from "./UploadWidget";

interface UploadTemplateProps {
  onSubmit: () => void;
}
function UploadTemplate({ onSubmit }: UploadTemplateProps): JSX.Element {
  const handleFileSelect = async (acceptedFiles: File[]): Promise<void> => {
    const file = acceptedFiles[0];
  };
  return (
    <>
      <UploadWidget handleFileSelect={handleFileSelect} />
    </>
  );
}

export default UploadTemplate;
