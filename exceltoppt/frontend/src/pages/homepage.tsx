import Image from 'next/image';
import { Inter } from 'next/font/google';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Header from '@/components/header';
import Progressbar from '@/components/progressbar';
import { FaCloudUploadAlt } from 'react-icons/fa';
import { FileText } from 'react-feather';
import { useRouter } from 'next/router';
import { ChevronRight } from "@/icons/ChevronRight";
import { UploadCloud02 } from "@/icons/UploadCloud02";
import { XClose } from "@/icons/XClose";

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const [sheetCount, setSheetCount] = useState<number | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [manifest, setManifest] = useState(false);

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
      setManifest(true);
      const q_params = "file_name=" + encodeURIComponent(selectedFileName?.split(".")[0]) + "&file_path=" + "data/Excel/" + encodeURIComponent(selectedFileName) + "&save_dir=" + "data/Manifest";
      const response = await axios.get(`http://localhost:8000/generateManifest/?${q_params}`);

      if (response.status === 200) {
        console.log("Manifest Generated..");

        const sheetNames = Array.isArray(response.data.sheet_names)
          ? response.data.sheet_names
          : [response.data.sheet_names];
        console.log(typeof sheetNames);
        setManifest(false);
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
          console.log(response.data);
          setSelectedFileName(response.data.file_name);
          setSheetCount(response.data.sheets_count);
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
      {manifest ? (
        <div className="upload-container-main">
          <div className="breadcrumb-container">
            <a>Ingest</a>
            <span className="separator"></span>
            <ChevronRight className="icon-instance" color="#A1A1AA" />
            <span className="current-page"> AI DeckBuilder</span>
          </div>
          <div className="manifest-header2">Generating Manifest...</div>
          <div className="loadingContainer2">

            <div className="spinner2"></div>
          </div>
        </div>
      ) : (
        <div className="upload-container-main2">
          <div className="breadcrumb-container">
            <a>Ingest</a>
            <span className="separator"></span>
            <ChevronRight className="icon-instance" color="#A1A1AA" />
            <span className="current-page"> AI DeckBuilder</span>
          </div>
          <div className="progress-bar-container">
            <Progressbar current={1} />
          </div>
          <div className="upload-container">
            <div className="upload-header-container">
              Upload
            </div>
            <div className="upload-widget">
              <div className="upload-icon">
                <UploadCloud02 className="upload-cloud-icon" onClick={handleFileInputChange}  />
              </div>
              <p className="upload-text" style={{ cursor: "pointer" }} onClick={handleFileInputChange}>
                Click to upload Excel File
              </p>
              {/*<p className="upload-sub-text">or drag and drop your .xlsx file</p>*/}
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
              <div className="file-frame">
                <div className="div">
                  <div className="div-2">
                    <img className="bxs-file-pdf" alt="Bxs file pdf" src="img/xlsx-file-format-svgrepo-com.svg" />
                    <div className="text-wrapper">{selectedFileName}</div>
                  </div>
                 {/* <XClose className="x-close" onClick={handleCanclebutton} />*/}
                </div>
                <div className="sidebar-divider"></div>
                <div className="div-3">
                  <div className="text-wrapper-2">{sheetCount} Sheets Found</div>
                  <div className="div-4">
                    <div className="text-wrapper-2">Size:</div>
                    <div className="div-wrapper">
                      <div className="text-wrapper-3">{fileSize}</div>
                    </div>
                  </div>
                </div>
              </div>

            ) : null}
            <div className="uploadContainer2">

              <button className="action-button2" onClick={handleCanclebutton}>Cancel</button>
              <div className="space-padding"></div>
              <button className="action-button-align-right action-button" onClick={handleSubmitbutton}>Submit</button>

            </div>

          </div>
        </div>
      )}

    </div>
  );
}


