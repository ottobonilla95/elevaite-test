import Image from 'next/image';
import { Inter } from 'next/font/google';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Header from '@/components/header';
import Progressbar from '@/components/progressbar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useRouter } from 'next/router';

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const [sheetCount, setSheetCount] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();

  const handleFileInputChange = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleCanclebutton = () => {
    setSelectedFileName("");
    setSheetCount(0);
  };

  const handleSubmitbutton = async () => {
    try {
      console.log("Generating Manifest..");
      setIsLoading(true);
      const q_params = "file_name=" + encodeURIComponent(selectedFileName?.split(".")[0]) + "&file_path=" + "data/Excel/" +encodeURIComponent(selectedFileName) + "&save_dir=" + "data/Manifest";
      const response = await axios.get(`http://localhost:8000/generateManifest/?${q_params}`);

      if (response.status === 200) {
        console.log("Manifest Generated..");
        
        const sheetNames = Array.isArray(response.data.sheet_names)
                ? response.data.sheet_names
                : [response.data.sheet_names];
        console.log(typeof sheetNames);
        setIsLoading(false);
        router.push({
          pathname: '/reviewManifest',
          query: {
            fileName: selectedFileName?.split('.')[0],
            sheetNames: sheetNames
          }
      });
      }
    } catch (error) {
      setIsLoading(false);
      console.error('Error generating manifest:', error);
    }

  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setIsLoading(true);
    if (file) {


      // Send the file to the server using Axios
      const formData = new FormData();
      formData.append('file', file);

      try {
        console.log("Uploading File..");
        const response = await axios.post('http://localhost:8000/upload/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        console.log("File Uploaded..");
        if (response.status === 200) {
          console.log(response);
          setSelectedFileName(file.name);
          setSheetCount(response.data.sheet_names.length);
          
          setIsLoading(false);
        }


      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
  };

  return (
    <div className="app-container">
      <Header />
      <div className="upload-container-main">
        <div className="progress-bar-container">
          {/* step progress bar goes here */}
        </div>
        <div className="upload-container">
          <div className="upload-widget">
            <div className="upload-icon">
              {/* Your icon goes here */}
            </div>
            <p className="upload-text" onClick={handleFileInputChange}>
              Click to upload Excel File
            </p>
            <p className="upload-sub-text">or drag and drop your .xlsx file</p>
          </div>
          <input
            type="file"
            accept=".xlsx"
            style={{ display: 'none' }}
            ref={fileInputRef}
            onChange={handleFileSelect}
          />

          {isLoading ? (
            <div className="loadingContainer">
              <div className="spinner"></div>
            </div>
          ) : selectedFileName ? ( 
            <div className="file-list-container">
              <p className="fileNametext">{selectedFileName}</p>
              <div className="sidebar-divider"></div>
              {sheetCount !== null && (
                <p className="sheetCounttext">{sheetCount} sheets found</p>
              )}
            </div>
          ) : null}
          <div className="uploadContainer2">

            <button className="action-button-align-right2 action-button2" onClick={handleCanclebutton}>Cancel</button>
            <div className="space-padding"></div>
            <button className="action-button-align-right action-button" onClick={handleSubmitbutton}>Submit</button>

          </div>

        </div>
      </div>
    </div>
  );
}
