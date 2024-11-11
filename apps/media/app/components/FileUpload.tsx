import React, { ChangeEvent } from "react";
import { CommonButton, ChatbotIcons } from "@repo/ui/components";

interface FileUploadProps {
    onFileSelect: (file: File) => void; // Callback to pass the selected file back to the parent
    isUploading: boolean;  // Whether the file is uploading
    onUpload: () => void;  // Action when file is uploaded
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, isUploading, onUpload }) => {
    // Handle file selection and pass the file back to parent
    const handleFileChange = (event: ChangeEvent<HTMLInputElement>): void => {
        const file = event.target.files?.[0];
        if (file) {
            if (file.type.startsWith("image/") || file.type.startsWith("video/") || file.type === "image/gif") {
                onFileSelect(file);  // Pass the file to the parent
            } else {
                console.error("Unsupported file type, please select an image, video, or GIF.");
            }
        }
    };

    return (
        <div className="file-upload-container">
            <input
                type="file"
                accept="image/*,video/*,image/gif"
                onChange={handleFileChange}
                style={{ display: "none" }} 
                id="file-upload-input"
            />
            <CommonButton
                // className="expo  rt-button"
                onClick={() => document.getElementById("file-upload-input")?.click()} // Trigger file selection
                disabled={isUploading}
            >
                {isUploading ? <ChatbotIcons.SVGSpinner /> : <ChatbotIcons.SVGPaperClip />}
            </CommonButton>
        </div>
    );
};

export default FileUpload;
