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

  const sheetNamesArray: string[] = Array.isArray(sheetNames)
    ? sheetNames
    : typeof sheetNames === 'string'
      ? [sheetNames]
      : [];

  console.log("sheet:::", sheetNamesArray);

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
    console.log(q_params);
    try {
      console.log("getting yaml content..");
      const response = await axios.get(`http://localhost:8000/getYamlContent/?${q_params}`);

      if (response.status === 200) {
        console.log("yaml content received..");
        setYamlContent(response.data);
        console.log(yamlContent);
      }
    } catch (error) {
      console.error('Error getting Manifest Content:', error);
    }
  };

  const handleSubmitbutton = () =>{
    router.push({
      pathname: '/generatePPT',
      query: {
        excel_file: fileName+".xlsx",
        manifest_file: activeSheet,
        folderName: fileName
      }
    });
    
  }
  const handleCanclebutton = () => {
    router.push('/')
  }
  return (
    <div className="app-container">
      <Header />
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
            <button className="action-button-align-right action-button" onClick={handleSubmitbutton}>Submit</button>
        </div>
      </div>
    </div>
  );
}
