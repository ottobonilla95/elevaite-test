import Image from 'next/image';
import Header from '../components/header';
import Template from '../components/template';
import ImageGallery from '../components/ImageGallery';
import SessionDalleForm from '@/components/sessionDalleForm';


import { FaCloudUploadAlt, FaArrowRight } from 'react-icons/fa';
import React, { useState, useEffect } from 'react';

import Router from 'next/router';


export default function Home() {

  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedButtonValue, setSelectedButtonValue] = useState<string | null>(null);
  const [selectedGenderValue, setSelectedGenderValue] = useState<string | null>(null);

  const handleSelectedTemplate = (imageName: string) =>{
    setSelectedTemplate(imageName);
  };

 

  //handling selection of Size  
  const handleButtononClick =(value: string) => {
    setSelectedButtonValue(value);
    
  };

  //handling selection of gender
  const handleGenderClick = (value: string) => {
    setSelectedGenderValue(value);
  };

 
    const handleContinueClick = () => {
      if(selectedTemplate === null){
        alert("Please select one of the ad banners to proceed!")
      } else{
        Router.push({
          pathname: '/step2',
          query: { template: selectedTemplate}
        })
      }   
    };

    const handleSessionComplete = (success: boolean) => {
    
      //console.log("inside session details refresh")
      /*if(refreshUserSessions){
        setRefreshUserSessions(true);
        console.log("inside handleSessionComplete - refresh user session: " +refreshUserSessions);
      } else {
        setRefreshUserSessions(false);
        console.log("inside handleSessionComplete - refresh user session: " +refreshUserSessions);
      }*/
      
      
  
    }

  return (
    <main>
      HELLO
      <SessionDalleForm timestamp="1695068839795" onSessionComplete={handleSessionComplete} />
      
    </main>
  )
}
