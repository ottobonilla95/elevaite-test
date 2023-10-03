import Header from '../components/header';
import FileUpload from '@/components/FileUpload';
import ImagePlaceholder from '../components/ImagePlaceholder';
import ImageGallery2 from '../components/ImageGallery2';
import { FaCloudUploadAlt, FaArrowLeft } from 'react-icons/fa';
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import GeneratedImages2 from '../components/generatedImages2';
import { GetServerSideProps, NextPage } from "next";
import fs from "fs/promises";
import path from "path";
import DalleFormEdit from '../components/DalleFormEdit';
import DalleFormNew from '@/components/DalleFormNew';
import { useSession } from 'next-auth/react';
import UserSessionsSummary from '@/components/userSessionsSummary';
import { time } from 'console';



/*interface ImageData {
  url: string;
}

interface ApiResponse {
  timestamp: number;
  data: ImageData[];
}*/

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
  const [preselectornew, setPreselectorNew] = useState<string | null>("preselect");
  const [graphicorinp, setGraphicorinp] = useState<string | null>("graphic");
  //const [result, setResult] = useState<ApiResponse | null>(null);
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
  const [selectedLLMValue, setSelectedLLMValue] = useState('DALL·E 2');
  const [sizeValue, setSizeValue] = useState('1024x1024');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isDropdownOpen2, setIsDropdownOpen2] = useState(false);
  const [refreshGallery, setRefreshGallery] = useState<boolean>(false);
  const [refreshUserSessions, setRefreshUserSessions] = useState<boolean>(false);
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  //const [userSessions, setUserSessions] = useState<ApiResponse | null>(null);

  const { data: session } = useSession();
  const userName = session?.user?.email?.split("@")[0];
  
  console.log("refresh user session - initially: " +refreshUserSessions);


  const router = useRouter();
  //const template = router.query.template as string;
  let dimensions: string = "";

  //get dimensions from the template
  const regex = /(\d+x\d+)px/;
  //const matches = template.match(regex);
  /*if (matches && matches.length > 1) {    
    dimensions = matches[1];
    
  } */
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
      await axios.post("/api/image", formData);
      //console.log(data);
    } catch (error: any) {
      console.log(error.response?.data);
    }
    setUploading(false);
  };

  const handleSessionSelect = (timestamp: number) => {
    setSelectedSession(timestamp);
  }

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
  const handleSelectedTemplate = (imageName: string) => {
    setSelectedTemplate(imageName);
    setLoading(0);

  };
  const options = ['DALL·E 2', 'MidJourney', 'Adobe FireFly'];
  const optionsSize = ['1024x1024', '256x256', '512x512'];

  const toggleDropdown1 = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const toggleDropdown2 = () => {
    setIsDropdownOpen2(!isDropdownOpen2)
  }

  const handleOptionClick = (option: string) => {
    setSelectedLLMValue(option);
    //console.log(selectedLLMValue);
    setIsDropdownOpen(false);
  };

  const handleSizeOptionClick = (option: string) => {
    setSizeValue(option);
    //console.log(sizeValue);
    setIsDropdownOpen2(false);
  }



  //handling selection of Size  
  const handleSizeonClick = (value: string) => {
    setSelectedSizeValue(value);

  };

  //handling selection of Content Type  
  const handleContentTypeonClick = (value: string) => {
    setContentType(value);

  };

  //handling selection of gender
  const handleGenderClick = (value: string) => {
    setSelectedGenderValue(value);
  };

  const handlePreorNewClick = (value: string) => {
    setPreselectorNew(value);
    setSelectedTemplate(null);

  }

  const handleGraphicorInp = (value:string) => {
    setGraphicorinp(value);
    setSelectedTemplate(null);
  }

  const handleUploadComplete = (success: boolean) => {
    //console.log("inside handleUploadComplete");
    setRefreshGallery((prev) => !prev);

  }
  const handleBackClick = () => {
    router.push('/CreativeBriefList');
  }

  const handleSessionComplete = (success: boolean) => {
    
    //console.log("inside session details refresh")
    /*if(refreshUserSessions){
      setRefreshUserSessions(true);
      console.log("inside handleSessionComplete - refresh user session: " +refreshUserSessions);
    } else {
      setRefreshUserSessions(false);
      console.log("inside handleSessionComplete - refresh user session: " +refreshUserSessions);
    }*/
    setRefreshUserSessions((prev) => !prev);
    

  }

  const handlenavigate= () => {
    router.push('/test');

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





  return (
    <main>
      <Header selectedImageCount={0} selectedImages = {[]}/>
      <div className="app-container">

        <div className="sidebar-container">
          
          <div className="banner-header">
            <FaArrowLeft className="left-arrow" onClick={handleBackClick}/>
            <p> AD BANNER TEMPLATES </p>
          </div>
          

          <p className="sub-text"> Choose a template </p>

          <div className="llm-container">
            <p className="sub-text2"> LLM </p>
            <div className="custom-dropdown">
              <div className="selected-option" onClick={toggleDropdown1}>
                <span className="option-text">{selectedLLMValue}</span>
                <span className={`arrow ${isDropdownOpen ? 'open' : ''}`}>&#9660;</span>
              </div>
              {isDropdownOpen && (
                <div>
                  {options.map((option) => (
                    <div
                      key={option}
                      className={`dropdown-item ${selectedLLMValue === option ? 'selected' : ''}`}
                      onClick={() => handleOptionClick(option)}>
                      {option}
                    </div>
                  ))}
                </div>
              )}
                  </div>
            {/*<div className="space-padding3"></div>
              <div className="dropdown-containernew2">
              <div className={`dropdownnew ${isDropdownOpen ? 'open' : ''}`} onClick={toggleDropdown1}>
                <span>{selectedLLMValue || 'Select an option'}</span>
                <span className="dropdown-arrow">&#9660;</span>
              </div>
              {isDropdownOpen && (
                <ul className="dropdown-menu-new">
                  {options.map((option, index) => (
                    <li
                      key={index}
                      className="dropdown-item-new"
                      onClick={() => handleOptionClick(option)}
                    >
                      {option}
                    </li>
                  ))}
                </ul>
              )}
                  </div>*/}
          </div>
          <div className="llm-container">
            <div className="input-container2">
              <div className="radiobuttonGroup">
                <button className={graphicorinp === 'graphic' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleGraphicorInp('graphic')}>
                  Graphic
                </button>
                <button className={graphicorinp === 'inp' ? "radiobuttonselected" : "radiobutton"} onClick={() => handleGraphicorInp('inp')}>
                  In-Painting
                </button>
              </div>
            </div>

          </div>

          
          <div className="space-padding"></div>
          <hr className="sidebar-divider"></hr>
          {graphicorinp === 'inp' ? (<div>
            
          
            <div className="llm-container">
              <p className="sub-text3"> Size </p>
              <div className="custom-dropdown">
  
                <div className="selected-option" onClick={toggleDropdown2}>
                  <span className="option-text">{sizeValue}</span>
                  <span className={`arrow ${isDropdownOpen2 ? 'open' : ''}`}>&#9660;</span>
                </div>
                {isDropdownOpen2 && (
                  <div>
                    {optionsSize.map((option) => (
                      <div
                        key={option}
                        className={`dropdown-item ${sizeValue === option ? 'selected' : ''}`}
                        onClick={() => handleSizeOptionClick(option)}>
                        {option}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
  
            <div className="llm-container">
              <p className="sub-text2">Template </p>
              <div className="input-container">
                <div className="radiobuttonGroup">
                  <button className={preselectornew === 'preselect' ? "radiobuttonselected" : "radiobutton"} onClick={() => handlePreorNewClick('preselect')}>
                    Preselect
                  </button>
                  <button className={preselectornew === 'new' ? "radiobuttonselected" : "radiobutton"} onClick={() => handlePreorNewClick('new')}>
                    New
                  </button>
                </div>
              </div>
  
            </div>
            <div className="space-padding"></div>
            <hr className="sidebar-divider"></hr>
  
            {preselectornew === 'new' ?
              (
                <div>
  
                  <FileUpload onFileSelected={handleFileSelected} fileLocation={`templates/${sizeValue}`} onUploadComplete={handleUploadComplete} />
  
  
  
                  <div className="space-padding"></div>
                  <hr className="sidebar-divider"></hr>
                  <div className="scrollable-container">
                    <ImageGallery2 onImageSelect={handleSelectedTemplate} fileLocation={`templates/${sizeValue}`} refresh={refreshGallery} />
                  </div>
                </div>
  
              ) :
  
              (
                <div className="scrollable-container">
                  <ImageGallery2 onImageSelect={handleSelectedTemplate} fileLocation={sizeValue} refresh={refreshGallery} />
                </div>
              )
            }
            <div className="space-padding"></div>
            <hr className="sidebar-divider"></hr>
  
            {/*<UserSessionsSummary userName={userName} llm="DALLE2" refresh={refreshUserSessions} onSessionSelect={handleSessionSelect}/>
            {selectedSession !== null && (
            <p>Selected Timestamp: {selectedSession}</p>
            )}*/}
          </div>): (<></>)}
          
        </div>

        <div className="chat-container">
          {
            graphicorinp === 'inp' ? (
              <>
                {selectedTemplate ?
            (
              <ImagePlaceholder folderName={preselectornew === 'new' ? `templates/${sizeValue}` : sizeValue} fileLocation={selectedTemplate} />
            ) :
            (
              <div
                style={{
                  width: '250px',
                  height: '250px',
                  backgroundColor: 'lightgray',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid black'
                }}>
                Choose a template to start<span className="required">*</span>
              </div>
            )}
              </>
            ) : null
          }
          <div className="space-padding"></div>
          {selectedLLMValue === 'DALL·E 2' ? ( 
            graphicorinp === 'inp' ? 
            (<DalleFormEdit folderName={preselectornew === 'new' ? `templates/${sizeValue}` : sizeValue} template={selectedTemplate === null ? "" : selectedTemplate} size={sizeValue} onSessionComplete={handleSessionComplete} />) : (
            <DalleFormNew  onSessionComplete={handleSessionComplete}/>) ):<div> TBD </div>}
          {/*<button onClick={handlenavigate}>click</button>*/}



        </div>
      </div>
    </main>
  )
} 