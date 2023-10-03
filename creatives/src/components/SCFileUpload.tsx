import React, { useRef, useState } from 'react';
import { FaCloudUploadAlt, FaRegTrashAlt } from 'react-icons/fa';
import axios from 'axios';

interface SCFileUploadProps {
  onFileUpload: (url: string) => void; // Function to pass the URL to the parent component
}

const SCFileUpload: React.FC<SCFileUploadProps> = ({ onFileUpload }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploadSuccess, setUploadSuccess] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);

  const handleUploadClick = () => {
    setErrorMessage(null);
    setUploadSuccess(null); // Set to null to indicate uploading is in progress
    inputRef.current?.click();
  };

  const handleFileSelect = async () => {
    if (inputRef.current && inputRef.current.files) {
      const selectedFile = inputRef.current.files[0];

      if (selectedFile) {
        
         // const response = await axios.get('http://localhost:3000/api/convertFiletoUrl')

       

        
        setUploadedFileName(selectedFile.name);
      }
    }
  };

  const handleDeleteClick = () => {
    // Add logic to delete the uploaded file if needed.
    // You may want to clear the state and notify the parent component.
    setFileUrl(null);
    setUploadedFileName(null);
  };

  return (
    <div className="sc-image-gallery-container">
     
      <div className="sc-uploadContainer">
        <input
          type="file"
          accept=".png"
          style={{ display: 'none' }}
          ref={inputRef}
          onChange={handleFileSelect}
        />
        <FaCloudUploadAlt className="uploadIcon" onClick={handleUploadClick} />

        <button className="upload-button" onClick={handleUploadClick}>
          Upload File
        </button>
      </div>

      {uploadSuccess === false ? (
        <div style={{ alignItems: 'center', color: 'black', padding: '10px' }}>
          Error: {errorMessage}
        </div>
      ) : uploadedFileName ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            color: 'black',
            padding: '10px',
            border: '1px solid #ccc',
            borderRadius: '5px',
            marginTop: '10px',
            marginLeft: '50px',
            width: '100px'
          }}
        >
          Uploaded File: {uploadedFileName}
          <button
            style={{ marginLeft: '10px', background: 'none', border: 'none', cursor: 'pointer' }}
            onClick={handleDeleteClick}
          >
            <span role="img" aria-label="Delete">
              <FaRegTrashAlt />
            </span>
          </button>
        </div>
      ) : null}
    </div>
  );
};

export default SCFileUpload;
