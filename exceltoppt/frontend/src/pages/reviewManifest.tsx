import Image from 'next/image';
import { Inter } from 'next/font/google';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Header from '@/components/header';
import Progressbar from '@/components/progressbar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();
  const { fileName, sheetNames } = router.query;
  const [isLoading, setIsLoading] = useState(false);

  const sheetNamesArray: string[] = Array.isArray(sheetNames)
    ? sheetNames
    : typeof sheetNames === 'string'
      ? [sheetNames]
      : [];



  const [activeSheet, setActiveSheet] = useState<string | null>(null);
  const [yamlContent, setYamlContent] = useState<string | null>(null);

  useEffect(() => {
    // When the component mounts, select the first sheet if available
    if (sheetNamesArray.length > 0) {
      handleSheetClick(sheetNamesArray[0]);
    }
  }, [sheetNamesArray]);

  const handleSheetClick = async (sheetName: string) => {
    setActiveSheet(sheetName);
    const encodedYamlFile = encodeURIComponent(sheetName)

    console.log("Encoded: ", encodedYamlFile);
    const q_params = "file_name=" + fileName + "&yaml_file=" + encodedYamlFile;

    try {
      console.log("getting yaml content..");
      const response = await axios.get(`http://localhost:8000/getYamlContent/?${q_params}`);

      if (response.status === 200) {
        console.log("yaml content received..");
        setYamlContent(response.data);

      }
    } catch (error) {
      console.error('Error getting Manifest Content:', error);
    }
  };

  const handleSubmitbutton = async (fileName: string | string[] | undefined, activeSheet: string | null) => {
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
      const q_params = "excel_file=" + encodedExcelFile + ".xlsx&manifest_file=" + encodedManifestFile + "&folder_name=" + encodedExcelFile;
  
      try {
        console.log("generating ppt..");
        setIsLoading(true);
        const response = await axios.get(`http://localhost:8000/generatePPT/?${q_params}`);
  
        if (response.status === 200) {
          console.log("ppt generated successfully");
          setIsLoading(false);
          console.log(response);
          router.push({
            pathname: '/generatePPT',
            query: {
              ppt_file: response.data,
              excel_file: fileName + ".xlsx",
              sheet_name: activeSheet
            }
          });
        }
      } catch (error) {
        setIsLoading(false);
        console.log("Error generating Manifest Content: " + error);
      }
    }
  };
  


  const handleCanclebutton = () => {
    router.push('/')
  }
  return (
    <div className="app-container">
      <Header />

      {isLoading ? (
        <div className="upload-container-main">
          <div className="manifest-header2">Generating Presentation</div>
          <div className="loadingContainer2">

            <div className="spinner2"></div>
          </div>
        </div>
      ) : (
        <div className="upload-container-main">
          <div className="progress-bar-container">
            {/* Step progress bar goes here */}
          </div>
          <div className="manifest-header">Manifest Preview</div>
          <div className="manifest-container">
            <div>
              <pre>{yamlContent}</pre>
            </div>
            <div>
              <div className="manifest-header-container">
                Manifest List
              </div>
              <div className="manifest-subheader-container">
                File: {fileName}
              </div>

              <div className="sheet-names-container">
                {sheetNamesArray.map((sheetName, index) => (
                  <div
                    key={index}
                    className={`sheet-name ${activeSheet === sheetName ? 'active' : ''}`}
                    onClick={() => handleSheetClick(sheetName)}
                  >

                    {sheetName}
                    <button className="edit-button">Edit</button>


                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="button-container">
            <button className="action-button-align-right2 action-button2" onClick={handleCanclebutton}>Cancel</button>
            <div className="space-padding"></div>
            <button className="action-button-align-right action-button" onClick={() => handleSubmitbutton(fileName, activeSheet)}>Submit</button>
          </div>
        </div>
      )}

    </div>
  );
}
