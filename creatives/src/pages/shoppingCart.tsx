import React, { useState, useEffect, useReducer } from 'react';
import { useRouter } from 'next/router';
import Header from '@/components/header';
import ShoppingCartImages from '../components/ShoppingCartImages';
import { FaArrowLeft } from 'react-icons/fa';
import SCFileUploadThumb from '@/components/SCFileUploadThumb';
import axios from 'axios';
import { useSession } from 'next-auth/react';


export default function ShoppingCart() {
  //console.log("Component rendered");
  const router = useRouter();
  const { query } = router;
  const { url, count } = query;
  const uList = url as string[];
  const stringifiedQuery = {
    count: count?.toString() || '',
    url: url?.toString() || ''
};

  const selectedImageCount = parseInt(stringifiedQuery.count, 10) || 0;
  const {data:session} = useSession();
  const userName = session?.user?.email?.split("@")[0];

  const [offeringMsg, setOfferingMsg] = useState("");
  const [cta, setCTA] = useState("");
  const [ea, setEA] = useState("");
  const [pFileUrl, setPFileUrl] = useState<string | null>(null);
  const [bFileUrl, setBFileUrl] = useState<string | null>(null);

  const handleProductFileUpload = (url: string) => {
    // This function will receive the URL from SCFileUpload component
    setPFileUrl(url);
  };

  const handleBrandFileUpload = (url: string) => {
    setBFileUrl(url);
  };

  const handleAssignClick = async () => {
    console.log("calling api...");
    try {
      const res = await axios.get('http://localhost:3000/api/createCreativeBrief', {
        params: {
          offeringMsg: offeringMsg,
          cta: cta,
          ea: ea,
          userName: userName,
          pFileUrl: pFileUrl,
          bFileUrl: bFileUrl,
          urlList: uList.join(',')
        }
      });
  
      if(res.status === 200){
        router.push('/CreativeBriefList');
      }
    } catch (error) {
      console.log("error from api: " + error);
    }
  };

 
  const urlList = Array.isArray(stringifiedQuery.url) ? stringifiedQuery.url : [stringifiedQuery.url];
 

  const handleSelectedImagesCountChange = () => { };

  const handleBackClick = () => {
    router.push('/homepage');
  }
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { id, value } = e.target;

    // Use a switch statement or if-else to determine which input field to update
    switch (id) {
      case 'offeringMsg':
        setOfferingMsg(value);
        break;
      case 'cta':
        setCTA(value);
        break;
      case 'ea':
        setEA(value);
        break;
      default:
        break;
    }
  };

  return (
    <div>
      <Header selectedImageCount={selectedImageCount} selectedImages={urlList} />
      <div className="app-container">
        <div className="chat-container2">
          <div className="header-banner">
            <div className="header-heading">CREATIVE BRIEF</div>
          </div>
          <FaArrowLeft className="left-arrow2" onClick={handleBackClick} />
          <div className="space-between"></div>
          <div className="sc-parent-container">
            <div className="sc-sidebar-container">
              <div className="banner-header2">
                <p> CREATIVES </p>
              </div>
              <ShoppingCartImages urls={url} />
              <div className="space-padding"></div>
              <hr className="sidebar-divider"></hr>
              <div className="banner-header2">
                <p> PRODUCT IMAGE </p>
              </div>
              <SCFileUploadThumb fileType = "product" onFileUpload={handleProductFileUpload} />
              <div className="space-padding"></div>
              <hr className="sidebar-divider"></hr>
              <div className="banner-header2">
                <p> BRAND IMAGE </p>
              </div>
              <SCFileUploadThumb fileType = "brand" onFileUpload={handleBrandFileUpload} />
            </div>
            <div className="sc-sidebar-container">
              <div className="space-padding"></div>
              <div className="space-padding"></div>
              <div className="form-row">
                <label htmlFor="offeringMsg">Offering Message<span className="required">*</span></label>
                <input className="large-input-field" type="text" id="offeringMsg" value={offeringMsg} onChange={handleInputChange}></input>
              </div>
              <div className="form-row">
                <label htmlFor="cta">Click to Action<span className="required">*</span></label>
                <input className="basic-input-field" type="text" id="cta" value={cta} onChange={handleInputChange}></input>
              </div>
              <div className="space-padding"></div>
              <div className="form-row">
                <label htmlFor="ea">Asignee Email<span className="required">*</span></label>
                <input className="basic-input-field" type="text" id="ea" value={ea} onChange={handleInputChange}></input>
              </div>
              <div className="form-row">
                <div className="uploadContainer2">
                  <button onClick={handleAssignClick} className="button-align-right work-bench-button">
                    <p>Assign</p>
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}