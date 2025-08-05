"use client";

import React, { useRef, useState } from "react";
import { X } from "lucide-react";
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
  uploadEndpoint?: string;
}

function UploadModal({
  isOpen,
  onClose,
  uploadEndpoint,
}: UploadModalProps): JSX.Element | null {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isWarningFlashing, setIsWarningFlashing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = (): void => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ): void => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles: UploadingFile[] = Array.from(files).map((file) => {
        // Convert file size to readable format
        const sizeInMB = file.size / (1024 * 1024);
        const sizeFormatted =
          sizeInMB >= 1
            ? `${sizeInMB.toFixed(1)} MB`
            : `${(file.size / 1024).toFixed(1)} KB`;

        return {
          id: `${Date.now().toString()}-${Math.random().toString()}`,
          name: file.name,
          size: sizeFormatted,
          progress: 0,
          completed: false,
        };
      });

      setUploadingFiles((prevFiles) => [...prevFiles, ...newFiles]);

      // Start upload for each file
      newFiles.forEach((uploadingFile, index) => {
        const actualFile = Array.from(files)[index];
        simulateFileUpload(uploadingFile.id, actualFile);
      });
    }

    // Reset the input value so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadFileToBackend = async (
    file: File,
    fileId: string
  ): Promise<void> => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:9004";
      const endpoint =
        uploadEndpoint ?? `${backendUrl.replace(/\/$/, "")}/api/files/upload`;

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      // Mark file as completed
      setUploadingFiles((prevFiles) =>
        prevFiles.map((f) =>
          f.id === fileId ? { ...f, progress: 100, completed: true } : f
        )
      );
    } catch (error) {
      // Mark file as failed
      setUploadingFiles((prevFiles) =>
        prevFiles.map((f) =>
          f.id === fileId ? { ...f, progress: 0, completed: false } : f
        )
      );
    }
  };

  const simulateFileUpload = (fileId: string, file: File): void => {
    void uploadFileToBackend(file, fileId);

    // Show progress animation
    const interval = setInterval(() => {
      setUploadingFiles((prevFiles) => {
        const updatedFiles = prevFiles.map((fileItem) => {
          if (fileItem.id === fileId && !fileItem.completed) {
            const newProgress = Math.min(
              fileItem.progress + Math.random() * 15,
              90
            );
            return {
              ...fileItem,
              progress: newProgress,
            };
          }
          return fileItem;
        });

        // Clear interval if file is completed or we've reached 90%
        const targetFile = updatedFiles.find((f) => f.id === fileId);
        if (
          targetFile?.completed ??
          (targetFile && targetFile.progress >= 90)
        ) {
          clearInterval(interval);
        }

        return updatedFiles;
      });
    }, 200);
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

  const handleOverlayKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div
      className="upload-modal-overlay"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="button"
      aria-label="Close modal"
      tabIndex={0}
    >
      <div className="upload-modal-content">
        {/* Header */}
        <div className="upload-modal-header">
          <h1>Upload Files</h1>
          <button className="close-button" onClick={onClose} type="button">
            <X size={20} />
          </button>
        </div>

        {/* Upload Area */}
        <div className="upload-area">
          {/* Dropzone */}
          <div
            className="upload-dropzone"
            role="button"
            tabIndex={0}
            aria-label="Upload files by clicking or pressing Enter/Space"
            onClick={handleFileSelect}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleFileSelect();
              }
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = "#5f5f61";
              e.currentTarget.style.backgroundColor =
                "rgba(255, 255, 255, 0.03)";
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "#5f5f61";
              e.currentTarget.style.backgroundColor =
                "rgba(255, 255, 255, 0.03)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.2)";
              e.currentTarget.style.backgroundColor = "transparent";
            }}
            onBlur={(e) => {
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
                <strong>Files are still uploading.</strong> Please wait before
                proceeding.
              </div>
            )}

            {/* Render file items from state */}
            {uploadingFiles.length === 0 ? (
              <div className="no-files-message">No files uploaded yet</div>
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
                      className="file-icon"
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
                            style={{ width: `${file.progress.toString()}%` }}
                          />
                        </div>
                        <div
                          className={`progress-percentage ${
                            file.progress === 100 ? "completed" : ""
                          }`}
                        >
                          {Math.round(file.progress)}%
                        </div>
                      </>
                    ) : (
                      <div className="spacer" />
                    )}
                    <button
                      type="button"
                      className="delete-button"
                      onClick={() => {
                        handleDeleteFile(file.id);
                      }}
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
