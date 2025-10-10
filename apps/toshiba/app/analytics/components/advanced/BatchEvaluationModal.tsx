import { useState } from "react";
import { CommonButton, CommonModal } from "@repo/ui/components";
import "./BatchEvaluationModal.scss";

interface BatchEvaluationModalProps {
    onClose: () => void;
    onSubmit: (file: File) => void;
}

export function BatchEvaluationModal({ onClose, onSubmit }: BatchEvaluationModalProps): JSX.Element {
    const [file, setFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
        }
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const droppedFile = e.dataTransfer.files[0];
            if (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls')) {
                setFile(droppedFile);
            }
        }
    };

    const handleSubmit = () => {
        if (file) {
            onSubmit(file);
        }
    };

    return (
        <div className="batch-evaluation-modal-container">
            <h2 className="modal-title">Batch Evaluation</h2>
            
            <div 
                className={`upload-area ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <input 
                    type="file" 
                    id="file-upload" 
                    accept=".xlsx,.xls" 
                    onChange={handleFileSelect}
                    className="file-input"
                />
                
                {!file ? (
                    <div className="upload-prompt">
                        <div className="upload-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 16V8M12 8L9 11M12 8L15 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                <path d="M3 15V16C3 18.2091 4.79086 20 7 20H17C19.2091 20 21 18.2091 21 16V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        </div>
                        <label htmlFor="file-upload" className="upload-label">
                            Click to upload Excel file
                        </label>
                        <p className="upload-hint">or drag and drop your .xlsx file</p>
                    </div>
                ) : (
                    <div className="file-info">
                        <span className="file-name">{file.name}</span>
                        <button className="remove-file" onClick={() => setFile(null)}>×</button>
                    </div>
                )}
            </div>
            
            <div className="modal-actions">
                <CommonButton onClick={onClose}>Cancel</CommonButton>
                <CommonButton 
                    onClick={handleSubmit} 
                    disabled={!file}
                    className="evaluate-button"
                >
                    Evaluate
                </CommonButton>
            </div>
        </div>
    );
}