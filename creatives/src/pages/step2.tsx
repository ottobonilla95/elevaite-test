import Image from 'next/image';
import Header from '../components/header';
import FileUpload from '@/components/FileUpload';
import ImagePlaceholder from '../components/ImagePlaceholder';
import ImageGallery2 from '../components/ImageGallery2';
import { FaCloudUploadAlt, FaArrowRight } from 'react-icons/fa';
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import GeneratedImages2 from '../components/generatedImages2';
import { GetServerSideProps, NextPage } from "next";
import fs from "fs/promises";
import path from "path";


interface ImageData {
  url: string;
}

interface ApiResponse {
  created: number;
  data: ImageData[];
}

export const getServerSideProps: GetServerSideProps = async () => {
  const props = { dirs: [] };
  try {
    const dirs = await fs.readdir(path.join(process.cwd(), "/public/images"));
    props.dirs = dirs as any;
    return { props };
  } catch (error) {
    return { props };
  }
};

export default function Home() {

  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedSizeValue, setSelectedSizeValue] = useState<string | null>(null);
  const [selectedGenderValue, setSelectedGenderValue] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [urls, setUrls] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [theme, setTheme] = useState('');
  const [ta, setTa] = useState('');
  const [noi, setNoi] = useState('');
  const [loading, setLoading] = useState(0);
  const [selectedContentType, setContentType] = useState<string | null>(null);
  const [selectedColor, setColor] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedImage, setSelectedImage] = useState("");
  const [selectedFile, setSelectedFile] = useState<File>();
  const [messageError, setMessageError] = useState("");
  const [noiError, setNOIError] = useState("");
  const [sizeError, setSizeError] = useState("");
  const [selectedValue, setSelectedValue] = useState('DALL·E 2');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [refreshGallery, setRefreshGallery] = useState<boolean>(false);

  const router = useRouter();
  const template = router.query.template as string;
  let dimensions: string = "";

  //get dimensions from the template
  const regex = /(\d+x\d+)px/; 
  const matches = template.match(regex);
  if (matches && matches.length > 1) {    
    dimensions = matches[1];
    
  } 
  const [file, setFile] = useState<File | null>(null);
  const handleFileSelected = (file: File) => {
    setSelectedFile(file);
  };
  const handleUpload = async () => {
    setUploading(true);
    try {
      if (!selectedFile) return;
      const formData = new FormData();
      formData.append("myImage", selectedFile);
      const { data } = await axios.post("/api/image", formData);
      console.log(data);
    } catch (error: any) {
      console.log(error.response?.data);
    }
    setUploading(false);
  };

  const handleUploadButton = async () => {
    //const router = useRouter();
    router.push('test');
    /*console.log("upload button clicked");
    setUploading(true);
    try{
      if(!selectedFile) return;
      const formData = new FormData();
      formData.append("myTemplate", selectedFile);
      const{ data } = await axios.post("/api/upload?fileLocation=" + {dimensions}, formData); 
      console.log(data);
    } catch(error: any){
      console.log(error.response?.data);
    }
    setUploading(false);*/
  };
 

  

  //handling selected template
  const handleSelectedTemplate = (imageName: string) =>{
    setSelectedTemplate(imageName);
    setLoading(0);
   
  };
  const options = ['DALL·E 2', 'MidJourney', 'Adobe FireFly'];

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleOptionClick = (option: string) => {
    setSelectedValue(option);
    console.log(selectedValue);
    setIsDropdownOpen(false);
  };
  

  //handling selection of Size  
  const handleSizeonClick =(value: string) => {
    setSelectedSizeValue(value);
    
  };

  //handling selection of Content Type  
  const handleContentTypeonClick =(value: string) => {
    setContentType(value);
    
  };

  //handling selection of gender
  const handleGenderClick = (value: string) => {
    setSelectedGenderValue(value);
  };

  const handleUploadComplete = () => {
    setRefreshGallery((prev) => !prev);
  }

  //handling selected color 
  const handleColoronClick = (value: string) => {
    setColor(value);
  }
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { id, value } = e.target;
  
    // Use a switch statement or if-else to determine which input field to update
    switch (id) {
      case 'message':
        setMessage(value);
        break;
      case 'theme':
        setTheme(value);
        break;
      case 'noi':
        setNoi(value);
        break;
      case 'ta':
        setTa(value);
        break;
      default:
        break;
    }
  };
  
  //Dalle 2 Edit Images API Call
  const handleButtonClick = async () => {
    console.log("generate button clicked");
    /*if (!message) {
      console.log("inside message: "  + message);
      setMessageError("Please fill in this fields.");
    }
    if(!noi){
      console.log("inside !noi : " + noi);
      setNOIError("Please fill in this field.");
    }
    if(Number(noi) > 10){
      console.log("inside noi > 10: " + Number(noi));
      setNOIError("Image count cannot be more than 10");
    }
    if(!selectedSizeValue){
      console.log("inside size: " + selectedSizeValue);
      setSizeError("Please fill in this field.");
    }
    if(message && noi && noi <= '10' && selectedSizeValue){*/
      console.log("calling api");
      console.log(process.env.OPENAI_API_KEY);
    setLoading(1); 
    setMessageError('');
    setSizeError('');
    setNOIError('');
    try {

        
        const response = await axios.get('http://localhost:3000/api/imageEditorApi',{
          params: {
              folerName: dimensions,
              image: selectedTemplate,
              size: selectedSizeValue,
              n: noi,
              prompt: "A " +selectedColor+ " toned picture of "+ message + "The Content Type is " +selectedContentType+". This picture should be targetted to an audience with an age range between " + ta + " and toward  " + selectedGenderValue + " gender(s). The theme of this picture is " + theme ,
          },
      });
        setResult(response.data);
        console.log("Result from API Call: " + result);
        setLoading(2);
        
    } catch (error) {
        console.error('Error making API call:', error);
        setLoading(3);
    } 
  //}
};

  

  return (
    <main>
      <Header />
      <div className="app-container">
        <div className ="sidebar-container">
          <div className="banner-header">
            <p> AD BANNER TEMPLATES </p>
          </div>
          <p className="sub-text"> Step 2: Choose a template </p>
          <div className="uploadContainer">
            
            <FaCloudUploadAlt className="uploadIcon" />
            <label>
            <FileUpload onFileSelected={handleFileSelected} fileLocation={dimensions} onUploadComplete={handleUploadComplete}/>
              {selectedFile && (
                ""
              )}
            </label>
          </div>
          <hr className="sidebar-divider"></hr>
          <div className ="scrollable-container">
            <ImageGallery2 onImageSelect={handleSelectedTemplate} fileLocation={dimensions} refresh={refreshGallery} />
            
          </div>
          
          
        </div>
        <div className="chat-container">
        <div className="dropdown">
      <div className="selected-value" onClick={toggleDropdown}>
        {selectedValue} <div style={{ color: 'black', textAlign: 'right' }}>▼</div>
        
      </div>
      {isDropdownOpen && (
        <div>
          {options.map((option) => (
            <div
              key={option}
              className={`dropdown-item ${selectedValue === option ? 'selected' : ''}`}
              onClick={() => handleOptionClick(option)}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </div>
          {selectedTemplate ? 
            (
              <ImagePlaceholder folderName={dimensions} fileLocation= {selectedTemplate} />          
            ):
            (
              <div
                style={{
                    width: '250px',
                    height: '250px',
                    backgroundColor: 'lightgray',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}>
                Choose a template to start
            </div>
            )}
          <div className="space-padding"></div>
          {selectedValue === 'DALL·E 2' ? (
            <div className="form-container">

            <div className="form-row">
              <label className="form-label" htmlFor="messgae">
                Message
              </label>
              <div className="space-padding"></div>
              <div className="input-container">
              <input
                className={`form-largeinput ${messageError && 'error'}`}
                type="text"
                id="message"
                placeholder="enter your prompt"
                value={message}
                onChange={handleInputChange}
              />
              {messageError && (
                <div className="error-message">{messageError}</div>
              )}
              </div>
            
            </div>

            <div className="form-row">
              <label className="form-label" htmlFor="theme">
                Theme
              </label>
              <div className="space-padding2"></div>
              <input className="form-input" type="text" id="theme" placeholder="enter the theme of your campaign" value={theme} onChange={handleInputChange}></input>            
            </div>

            <div className="form-row">
            <label className="form-label" htmlFor="messgae">
                Target audience
              </label>
              <div className="space-padding"></div>
              <input className="form-input" type="text" id="ta" placeholder="20-30" value={ta} onChange={handleInputChange}></input>
              <div className="space-padding"></div>
              <label className="form-label" htmlFor="gender">
                Gender
              </label>
              <div className="space-padding"></div>
              <div className="input-container">
              <div className="radiobuttonGroup">

                <button className={selectedGenderValue === 'Male' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleGenderClick('Male')}>
                  Male
                </button>
                <button className={selectedGenderValue === 'Female' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleGenderClick('Female')}>
                  Female
                </button>

                <button className={selectedGenderValue === 'Both' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleGenderClick('Both')}>
                  Both
                </button>
              </div>     
              </div> 
            </div>

            <div className="form-row">
              <label className="form-label" htmlFor="size">
                Size
              </label>
              
              <div className="space-padding"></div>
              <div className="input-container">
              <div className="radiobuttonGroup">

                <button className={selectedSizeValue === '256x256' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleSizeonClick('256x256')}>
                  256x256
                </button>
                <button className={selectedSizeValue === '512x512' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleSizeonClick('512x512')}>
                  512x512
                </button>

                <button className={selectedSizeValue === '1024x1024' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleSizeonClick('1024x1024')}>
                  1024x1024
                </button>
                {sizeError && (
                <div className="error-message">{sizeError}</div>
              )}
              </div>
              </div>
             
            </div>
            <div className="form-row">
            <label className="form-label" htmlFor="messgae">
                Image Count
              </label>
              
              <div className="input-container">
              <input className={`form-input ${noiError && 'error'}`} type="text" id="noi" placeholder="4 [ maximum is 10 ]" value={noi} onChange={handleInputChange}></input>
              {noiError && (
                <div className="error-message">{noiError}</div>
              )}
              </div>
            </div>
            <div className="form-row">
              <label className="form-label" htmlFor="contentType">
                Content Type
              </label>
              <div className="input-container">
              <div className="radiobuttonGroup">

                <button className={selectedContentType === 'none' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleContentTypeonClick('none')}>
                  None
                </button>
                <button className={selectedContentType === 'photo' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleContentTypeonClick('photo')}>
                  Photo
                </button>

                <button className={selectedContentType === 'art' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleContentTypeonClick('art')}>
                  Art
                </button>

                <button className={selectedContentType === 'graphic' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleContentTypeonClick('graphic')}>
                  Graphic
                </button>
              </div>
              </div>
            </div>
            <div className="form-row">
              <label className="form-label" htmlFor="contentType">
                Color
              </label>
              
              <div className="radiobuttonGroup">

                <button className={selectedColor === 'none' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('none')}>
                  None
                </button>
                <button className={selectedColor === 'black & white' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('black & white')}>
                  B&W
                </button>

                <button className={selectedColor === 'muted' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('muted')}>
                  Muted
                </button>

                <button className={selectedColor === 'warm' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('warm')}>
                  Warm
                </button>
                <button className={selectedColor === 'cool' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('cool')}>
                  Cool
                </button>
                <button className={selectedColor === 'vibrant' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('vibrant')}>
                  Vibrant
                </button>
                <button className={selectedColor === 'pastels' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleColoronClick('pastels')}>
                  Pastels
                </button>
              </div>
            </div>
            
              
          </div> ) : (<div className="form-container"> <div style={{ color: 'white', textAlign: 'center' }}>TBD</div>
 </div>)}
          
          <div className="form-container2">
            <div className="uploadContainer2">
              <button onClick={handleButtonClick} className="button-align-right work-bench-button">
                <p>Generate</p>
              </button>
            </div>
            
            <div>
              
              <div className="form-container">
              {loading === 0 ? (
                  <h2 style={{ color: 'white', textAlign: 'center' }}>Generated images will appear here...</h2>
                ) : loading === 1 ? (
                  <h2 style={{ color: 'white', textAlign: 'center' }}>Generating images for "A {selectedColor} toned picture of {message}. The Content Type is {selectedContentType}. This picture should be targetted to an audience with an age range between {ta} and toward {selectedGenderValue} genders. The theme of this picture is {theme}"</h2>
                ) : loading === 2 && result !== null ? (
                  <GeneratedImages2 data={result.data} />
                ) : (
                  <h2 style={{ color: 'white' }}>Error while calling API</h2>
                )
              }

              </div>
            </div>
              
              
          </div>
        </div>
      </div>
    </main>
  )
}
