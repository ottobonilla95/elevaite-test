import React, { useRef, useState } from 'react';
import { FaCloudUploadAlt } from 'react-icons/fa';

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  fileLocation: string;
  onUploadComplete: (success: boolean) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelected, fileLocation, onUploadComplete }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const size = fileLocation.split("/")[1];
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleUploadClick = () =>{
    setErrorMessage(null);
    setUploadSuccess(true);
    inputRef.current?.click();
  };

  const handleFileSelect = async () => {
    if (inputRef.current && inputRef.current.files) {
      const selectedFile = inputRef.current.files[0];
  
      if (selectedFile) {
        const img = new Image();
        img.src = URL.createObjectURL(selectedFile);
  
        img.onload = () => {
          const width = img.width;
          const height = img.height;
  
          if (width !== parseInt(size.split('x')[0]) || height !== parseInt(size.split('x')[1])) {
            console.log(width+"x"+height+" ; " +size);
            //console.log("inside FileUpload - unsuccessful upload");
            setUploadSuccess(false);
            //console.log("after updating uploadSuccess " + uploadSuccess);
  
            // This may still show the old value of uploadSuccess in the console
            // because it's an asynchronous operation.
            onUploadComplete(false);
            setErrorMessage("Selected file does not satisfy the required dimensions");
          } else {
            //console.log("inside FileUpload - successful upload");
            onFileSelected(selectedFile);
  
            const formData = new FormData();
            formData.append('file', selectedFile);
  
            try {
              fetch(`/api/upload?fileLocation=${encodeURIComponent(fileLocation)}`, {
                method: 'POST',
                body: formData,
              })
                .then(response => {
                  if (response.ok) {
                    return response.json();
                  } else {
                    throw new Error('Failed to upload the file');
                  }
                })
                .then(data => {
                  console.log(data);
                  // Use the state updater function to update uploadSuccess
                  setUploadSuccess(true);
                  onUploadComplete(true);
                })
                .catch(error => {
                  console.error('Error uploading the file:', error);
                  // Use the state updater function to update uploadSuccess
                  setUploadSuccess(false);
                  onUploadComplete(false);
                });
            } catch (error) {
              console.error('Error uploading the file:', error);
              // Use the state updater function to update uploadSuccess
              setUploadSuccess(false);
              onUploadComplete(false);
            }
          }
        }
      }
    }
  };

  return (
    <div>
      <div className="uploadContainer">
        <FaCloudUploadAlt className="uploadIcon" />
        <input
          type="file"
          accept=".png"
          style={{ display: 'none' }}
          ref={inputRef}
          onChange={handleFileSelect}
        />
        <button className="upload-button" onClick={handleUploadClick}>Upload Template</button>
      </div>
      
      {uploadSuccess === false ? (<div style={{ alignItems: 'center', color: 'black', padding: '10px' }}>Error: {errorMessage}</div>) :("")}
    </div>
  );
};

export default FileUpload;
