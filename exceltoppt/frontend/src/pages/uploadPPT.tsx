import Image from 'next/image';
import { Inter } from 'next/font/google';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Header from '@/components/header';
import Progressbar from '@/components/progressbar';
import { FaCloudUploadAlt } from 'react-icons/fa';
import { FileText } from 'react-feather';
import { useRouter } from 'next/router';

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const [sheetCount, setSheetCount] = useState<number | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [manifest, setManifest] = useState(false);
  

  const router = useRouter();
  const { excel_file_name, manifest_file_name, folder_name } = router.query;

  const handleFileInputChange = () => {
    console.log("upload");
  };

  const handleCanclebutton = () => {
    router.push('/');
  };

  const handleSubmitbutton = async (fileName: string | string[] | undefined, activeSheet: string | null) => {
    console.log("button")
    if (fileName !== undefined && activeSheet !== null) {
      let encodedExcelFile: string;

      if (Array.isArray(fileName)) {
        // If fileName is an array, take the first element (you can modify this based on your requirement)
        encodedExcelFile = encodeURIComponent(fileName[0]);
      } else {
        // If fileName is a string, directly encode it
        encodedExcelFile = encodeURIComponent(fileName);
      }

      const encodedManifestFile = encodeURIComponent(activeSheet);
      const q_params = "excel_file=" + encodedExcelFile + "&manifest_file=" + encodedManifestFile + "&folder_name=" + encodedExcelFile.split(".")[0];
      console.log(q_params);
      try {
        console.log("generating ppt..");
        setManifest(true);
        const response = await axios.get(`http://localhost:8000/generatePPT/?${q_params}`);

        if (response.status === 200) {
          console.log("ppt generated successfully");
          setManifest(false);
          console.log(response);
          router.push({
            pathname: '/viewPPT',
            query: {
              ppt_file: response.data,
              excel_file: fileName ,
              sheet_name: activeSheet
            }
          });
          
        }
    }
      catch (error) {
        setIsLoading(false);
        console.log("Error generating Manifest Content: " + error);
      }
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
          setFileSize(response.data.file_size);

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
      {manifest ?  (
        <div className="upload-container-main">
        <div className="breadcrumb-container">
          <a>Ingest</a>
          <span className="separator"></span>
          {'>'}
          <span className="current-page"> AI DeckBuilder</span>
        </div>
        <div className="manifest-header2">Generating Presentation...</div>
        <div className="loadingContainer2">

          <div className="spinner2"></div>
        </div>
      </div>
      ):(
        <div className="upload-container-main">
        <div className="breadcrumb-container">
          <a>Ingest</a>
          <span className="separator"></span>
          {'>'}
          <span className="current-page"> AI DeckBuilder</span>
        </div>
        <div className="progress-bar-container">
          <Progressbar current={3} />
        </div>
        <div className="upload-container">
          <div className="upload-header-container">
            Upload PPT Template
          </div>
          <div className="upload-subheader-container">
          Select between uploading your own slide template or utilizing our generic template for quick, professional presentation.
          </div>
          <button className = "button-template" onClick={() => handleSubmitbutton(excel_file_name, manifest_file_name as string)}>Use Generic Template</button>
          <div className="sidebar-divider2"></div>
          <div className="upload-widget">
            <div className="upload-icon">
              <FaCloudUploadAlt className="upload-cloud-icon" />
            </div>
            <p className="upload-text" onClick={handleFileInputChange}>
              Click to upload PPT File
            </p>
            <p className="upload-sub-text">or drag and drop your .pptx file</p>
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
              {/*<div className="icon-container">
                <FileText />
          </div>*/}

              <p className="fileNametext">{selectedFileName}</p>
              {/*<div className="line-container"></div>*/}
              <div className="sidebar-divider"></div>
              {sheetCount !== null && (

                <div className="info-container">
                  <p className="sheetCounttext">{sheetCount} sheets found</p>
                  <p className="fileSizetext">Size: {fileSize}</p>
                </div>
              )}
            </div>
          ) : null}
          <div className="uploadContainer2">

            <button className="action-button2" onClick={handleCanclebutton}>Cancel</button>
            <div className="space-padding"></div>
            <button className="action-button-align-right action-button">Submit</button>

          </div>

        </div>
      </div>
      )}
      
    </div>
  );
}
