"use client";

import React, { useRef, useState } from "react";
import { X } from "lucide-react";
import { CommonButton } from "@repo/ui/components";
import "./UploadModal.scss";

interface UploadingFile {
  id: string;
  name: string;
  size: string;
  progress: number;
  completed: boolean;
}

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function UploadModal({ isOpen, onClose }: UploadModalProps): JSX.Element | null {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isWarningFlashing, setIsWarningFlashing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = (): void => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles: UploadingFile[] = Array.from(files).map((file) => {
        // Convert file size to readable format
        const sizeInMB = file.size / (1024 * 1024);
        const sizeFormatted = sizeInMB >= 1 
          ? `${sizeInMB.toFixed(1)} MB` 
          : `${(file.size / 1024).toFixed(1)} KB`;

        return {
          id: `${Date.now()}-${Math.random()}`,
          name: file.name,
          size: sizeFormatted,
          progress: 0,
          completed: false,
        };
      });

      setUploadingFiles((prevFiles) => [...prevFiles, ...newFiles]);

      // Start upload simulation for each file
      newFiles.forEach((file) => {
        simulateFileUpload(file.id);
      });
    }

    // Reset the input value so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const simulateFileUpload = (fileId: string): void => {
    const interval = setInterval(() => {
      setUploadingFiles((prevFiles) => {
        const updatedFiles = prevFiles.map((file) => {
          if (file.id === fileId && !file.completed) {
            const newProgress = Math.min(file.progress + Math.random() * 15, 100);
            return {
              ...file,
              progress: newProgress,
              completed: newProgress >= 100,
            };
          }
          return file;
        });

        // Clear interval if file is completed
        const targetFile = updatedFiles.find((f) => f.id === fileId);
        if (targetFile?.completed) {
          clearInterval(interval);
        }

        return updatedFiles;
      });
    }, 500);
  };

  const handleDeleteFile = (fileId: string): void => {
    setUploadingFiles((prevFiles) =>
      prevFiles.filter((file) => file.id !== fileId)
    );
  };

  const hasUploadingFiles = (): boolean => {
    return uploadingFiles.some((file) => !file.completed);
  };

  const handleOverlayClick = (e: React.MouseEvent): void => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="upload-modal-overlay" onClick={handleOverlayClick}>
      <div className="upload-modal-content">
        {/* Header */}
        <div className="upload-modal-header">
          <h1>Upload Files</h1>
          <button
            className="close-button"
            onClick={onClose}
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        {/* Upload Area */}
        <div className="upload-area">
          {/* Dropzone */}
          <div
            className="upload-dropzone"
            onClick={handleFileSelect}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = "#5f5f61";
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.03)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.2)";
              e.currentTarget.style.backgroundColor = "transparent";
            }}
          >
            <svg
              className="upload-icon"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
            </svg>
            <h3>Drag & Drop Files Here</h3>
            <p>or click to browse your files</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden-input"
              onChange={handleFileChange}
            />
          </div>

          {/* File List */}
          <div className="file-list">
            {/* Status message if files are still uploading */}
            {hasUploadingFiles() && (
              <div
                className={`warning-message ${isWarningFlashing ? "warning-flash" : ""}`}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                </svg>
                <strong>Files are still uploading.</strong> Please wait before proceeding.
              </div>
            )}

            {/* Render file items from state */}
            {uploadingFiles.length === 0 ? (
              <div
                style={{
                  color: "#999",
                  textAlign: "center",
                  padding: "1rem",
                }}
              >
                No files uploaded yet
              </div>
            ) : (
              uploadingFiles.map((file) => (
                <div key={file.id} className="file-item">
                  <div className="file-info">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="white"
                      style={{ marginRight: "0.75rem" }}
                    >
                      <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
                    </svg>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{file.size}</span>
                  </div>
                  <div className="file-actions">
                    {!file.completed ? (
                      <>
                        <div className="progress-container">
                          <div
                            className="progress-bar"
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                        <div
                          style={{
                            minWidth: "45px",
                            textAlign: "right",
                            fontSize: "14px",
                            fontWeight: "500",
                            color: file.progress === 100 ? "#30c292" : "#ccc",
                          }}
                        >
                          {Math.round(file.progress)}%
                        </div>
                      </>
                    ) : (
                      <div style={{ flex: 1 }}></div>
                    )}
                    <button
                      className="delete-button"
                      onClick={() => handleDeleteFile(file.id)}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadModal;
