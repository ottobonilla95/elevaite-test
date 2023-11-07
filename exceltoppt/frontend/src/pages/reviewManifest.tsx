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
  console.log("MANIFEST PAGE: ", sheetNames);
  console.log( typeof sheetNames);
  const sheetNamesArray: string[] = Array.isArray(sheetNames) ? sheetNames : sheetNames ? [sheetNames] : [];
  
  const [activeSheet, setActiveSheet] = useState<string | null>(null);
  const [yamlContent, setYamlContent] = useState<string | null>(null);

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
            File: {fileName}
            <div className="sheet-names-container">
              {(Array.isArray(sheetNames) ? sheetNames : []).map((sheetName: string, index: number) => (
                <div
                  key={index}
                  className={`sheet-name ${activeSheet === sheetName ? 'active' : ''}`}
                  onClick={() => handleSheetClick(sheetName)}
                >
                  {sheetName}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
