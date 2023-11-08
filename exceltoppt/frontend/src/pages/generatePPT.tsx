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
  const { excel_file, manifest_file, folderName } = router.query;
  
  useEffect(() => {
    // Define the data to be sent in the request body
    const data = {
      excel_file: excel_file,
      manifest_file: manifest_file,
      folder_name: folderName,
    };

    const q_param = ""
  }, [excel_file, manifest_file, folderName]);
  
  return (
    <div className="app-container">
      <Header />
      <div className="upload-container-main">
        <div className="progress-bar-container">
          {/* Step progress bar goes here */}
        </div>
        <div className="manifest-header">PPT Preview</div>
        <div className="manifest-container">
          <div>
            {excel_file}
            {manifest_file}
            {/* show ppt here */}
          </div>
          <div>
            
          </div>
        </div>
        
      </div>
    </div>
  );
}
