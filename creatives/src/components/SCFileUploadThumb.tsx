import React, { useRef, useState } from 'react';
import { FaCloudUploadAlt, FaRegTrashAlt } from 'react-icons/fa';
import axios from 'axios';

interface SCFileUploadProps {
  onFileUpload: (url: string) => void; // Function to pass the URL to the parent component
}

const SCFileUploadThumb: React.FC<SCFileUploadProps> = ({ onFileUpload }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploadSuccess, setUploadSuccess] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null); // Added state for thumbnail URL

  const handleUploadClick = () => {
    setErrorMessage(null);
    setUploadSuccess(null); // Set to null to indicate uploading is in progress
    inputRef.current?.click();
  };

  const handleFileSelect = async () => {
    if (inputRef.current && inputRef.current.files) {
      const selectedFile = inputRef.current.files[0];

      if (selectedFile) {
        const fileReader = new FileReader();

        fileReader.onload = (e) => {
          const thumbnail = e.target?.result as string;
          setThumbnailUrl(thumbnail); // Set the thumbnail URL in state
        };

        fileReader.readAsDataURL(selectedFile);
        const img = new Image();
        img.src = URL.createObjectURL(selectedFile);
        onFileUpload(img.src);

        // Continue with your file upload logic here
        // For example, send the file to the server and get the URL
        try {
          // const response = await axios.post('http://localhost:3000/api/uploadFile', selectedFile);
          // const fileUrl = response.data.fileUrl;
          // setFileUrl(fileUrl);
          setUploadedFileName(selectedFile.name);
          setUploadSuccess(true);
          if(fileUrl){
            onFileUpload(fileUrl);
          }
          // Pass the file URL to the parent component
        } catch (error) {
          setUploadSuccess(false);
          setErrorMessage("Error while trying to upload file");
        }
      }
    }
  };

  const handleDeleteClick = () => {
    // Add logic to delete the uploaded file if needed.
    // You may want to clear the state and notify the parent component.
    setFileUrl(null);
    setUploadedFileName(null);
    setThumbnailUrl(null); // Clear the thumbnail URL
  };

  return (
    <div className="sc-logo-gallery-container">
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
        <div style={{ color: 'black', padding: '10px' }}>
          Error: {errorMessage}
        </div>
      ) : uploadedFileName ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-start',
            color: 'black',
            padding: '10px',
            border: '1px solid #ccc',
            borderRadius: '5px',
            marginTop: '10px',
            marginBottom: '10px',
            marginLeft: '180px'
          }}
        >
          {thumbnailUrl && (
            <img
              src={thumbnailUrl}
              alt="Thumbnail"
              style={{
                width: '50px',
                height: '50px',
                marginRight: '10px',
              }}
            />
          )}
          <div>
          <span style={{ fontWeight: 'bold', fontStyle: 'italic' }}>
              File Name: </span>{uploadedFileName}
            
            <button
              style={{
                marginLeft: '10px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
              }}
              onClick={handleDeleteClick}
            >
              <span role="img" aria-label="Delete">
                <FaRegTrashAlt />
              </span>
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default SCFileUploadThumb;
