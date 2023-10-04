import React, { useRef, useState } from 'react';
import { FaCloudUploadAlt, FaRegTrashAlt } from 'react-icons/fa';


interface SCFileUploadProps {
  fileType: string,
  onFileUpload: (url: string) => void; 
}

const SCFileUploadThumb: React.FC<SCFileUploadProps> = ({ fileType, onFileUpload }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploadSuccess, setUploadSuccess] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null); 

  const handleUploadClick = () => {
    setErrorMessage(null);
    setUploadSuccess(null); 
    inputRef.current?.click();
  };

  const handleFileSelect = async () => {
    if (inputRef.current && inputRef.current.files) {
      const selectedFile = inputRef.current.files[0];

      if (selectedFile) {
        const fileReader = new FileReader();
        fileReader.onload = (e) => {
          const thumbnail = e.target?.result as string;
          setThumbnailUrl(thumbnail); 
        };

        fileReader.readAsDataURL(selectedFile);
        
        const formData = new FormData();
        formData.append('file', selectedFile);

        if( fileType === 'product') {
          fetch(`/api/upload?fileLocation=product`, {
            method: 'POST',
            body: formData,
          })
          .then(response => {
            if(response.ok) {
              //console.log(response.json());
              return response.json();
            } else {
              throw new Error('Failed to upload the file');
            }
          });
          
        }
        if( fileType === 'brand') {
          fetch(`/api/upload?fileLocation=brand`, {
            method: 'POST',
            body: formData,
          })
          .then(response => {
            if(response.ok) {
              return response.json();
            } else {
              throw new Error('Failed to upload the file');
            }
          });
          
        } 
        try {
          
          setUploadedFileName(selectedFile.name);
          setUploadSuccess(true);
          if(fileUrl){
            onFileUpload(fileUrl);
          }
          
        } catch (error) {
          setUploadSuccess(false);
          setErrorMessage("Error while trying to upload file");
        }
      }
    }
  };

  const handleDeleteClick = () => {
    setFileUrl(null);
    setUploadedFileName(null);
    setThumbnailUrl(null); 
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
