import Header from '@/components/header';
import { useRouter } from 'next/router';
import React, { useState, useEffect } from 'react';
import Loading from '@/components/loading';
import GeneratedImages2 from '@/components/generatedImages2';
import axios from 'axios';
import { FaArrowLeft } from 'react-icons/fa';

interface ImageData {
    url: string;
}

interface ApiResponse {
    created: number;
    data: ImageData[];
}



export default function GenerateImg() {
    const router = useRouter();
    const { query } = router;

    // Access the passed variables from the query object
    const {
        targetAudience,
        gender,
        seasonal,
        regional,
        occasion,
        description,
        contentType,
        color,
        size,
        imageCount,
        loading, 
        page
    } = query;



    const [ta, setTa] = useState(targetAudience);
    const [message, setMessage] = useState(description);
    const [noi, setNoi] = useState(imageCount);
    const [load, setLoad] = useState(loading);
    const [result, setResult] = useState<ApiResponse | null>();
    const [selectedContentType, setContentType] = useState<string | null>(contentType);
    const [selectedGenderValue, setSelectedGenderValue] = useState<string | null>(gender);
    const [selectedSeasonalValue, setSelectedSeasonalValue] = useState<string | null>(seasonal);
    const [selectedRegionalValue, setSelectedRegionalValue] = useState<string | null>(regional);
    const [selectedOccasionValue, setSelectedOccasionValue] = useState<string | null>(occasion);
    const [selectedColor, setColor] = useState<string | null>(color);
    const [selectedSizeValue, setSelectedSizeValue] = useState<string | null>(size);
    const [callApi, setCallApi] = useState(true);

    const[selectedImagesCount, setSelectedImagesCount] = useState(0);
    const[selectedImageUrl, setSelectedImageUrl] = useState<string[]>([]);
    const handleSelectedImagesCountChange = (count: number, selectedUrls: string[]) => {
        setSelectedImagesCount(count);
        setSelectedImageUrl(selectedUrls);
    }
    const handleContentTypeonClick = (value: string) => {
        setContentType(value);
    };

    
    const handleGenderClick = (value: string) => {
        setSelectedGenderValue(value);
    };
    
    const seasonalOptions = ['New Years', 'Valentines Day', 'Easter', 'July 4th', 'Labor day', 'Halloween', 'Thanksgiving', 'Chirstmas'];
    const [isSeasonalDDOpen, setIsSeasonalDDOpen] = useState(false);
    const toggleSeasonalDD = () => {
        setIsSeasonalDDOpen(!isSeasonalDDOpen);
    };
    const handleSeasonalClick = (value: string) => {
        setSelectedSeasonalValue(value);
        console.log(selectedSeasonalValue);
        setIsSeasonalDDOpen(!isSeasonalDDOpen);
    };

   
    const RegionalOptions = ['North America', 'South America', 'Europe', 'Asia', 'Africa', 'Australia'];
    const [isRegionalDDOpen, setIsRegionalDDOpen] = useState(false);
    const toggleRegionalDD = () => {
        setIsRegionalDDOpen(!isRegionalDDOpen);
    };
    const handleRegionalClick = (value: string) => {
        setSelectedRegionalValue(value);
        console.log(selectedRegionalValue);
        setIsRegionalDDOpen(!isRegionalDDOpen);
    };


    
    const OccasionalOptions = ['Breakfast', 'Lunch', 'Dinner', 'Office Party', 'Birthday Party'];
    const [isOccasionalDDOpen, setIsOccasionalDDOpen] = useState(false);
    const toggleOccasionalDD = () => {
        setIsOccasionalDDOpen(!isOccasionalDDOpen);
    };
    const handleOccasionClick = (value: string) => {
        setSelectedOccasionValue(value);
        console.log(selectedOccasionValue);
        setIsOccasionalDDOpen(!isOccasionalDDOpen);
    };

    
    const ColorOptions = ['None', 'Black & White', 'Muted', 'Warm', 'Cool', 'Vibrant', 'Pastels'];
    const [isColorDDOpen, setIsColorDDOpen] = useState(false);
    const toggleColorDD = () => {
        setIsColorDDOpen(!isColorDDOpen);
    };
    const handleColoronClick = (value: string) => {
        setColor(value);
        console.log(selectedColor);
        setIsColorDDOpen(!isColorDDOpen);
    };

    
    const handleSizeonClick = (value: string) => {
        setSelectedSizeValue(value);
    };

    const handleBackClick = () =>{
        router.push('/homepage');
    }
    useEffect(() => {
        const fetchData = async () => {
            try {
                console.log("CALLING API");
                let dalle_prompt = "A " + selectedColor + " toned picture of " + message +
                    ". This picture should be targetted to an audience with an age range between " + ta +
                    " and toward  " + selectedGenderValue +
                    " gender(s). The picture's theme is " + selectedSeasonalValue +
                    " applicable to audience living in " + selectedRegionalValue + " regions." +
                    "The Content Type is " + selectedContentType;

                const response = await axios.get('/api/imageGeneratorApioai', {
                    params: {
                        size: selectedSizeValue,
                        n: noi,
                        prompt: dalle_prompt,
                    },
                });
                console.log(response.data);
                setResult(response.data);
                setLoad('2');


            } catch (error) {
                console.log("Error making Generate API Call: ", error);
                setLoad('3');
            }
        };
        fetchData();
    }, []);

   
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
        const { id, value } = e.target;

        // Use a switch statement or if-else to determine which input field to update
        switch (id) {
            case 'message':
                setMessage(value);
                break;
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
            <Header selectedImageCount={selectedImagesCount} selectedImages={selectedImageUrl}/>
            <div className="app-container">
                <div className="sidebar-container2">
                    <div className="config-container">
                        <FaArrowLeft className="left-arrow" onClick={handleBackClick}/>
                        
                        <div className="header-style">DALL·E 2 CONFIGURATIONS</div>
                    </div>
                    
                    <hr className="sidebar-divider"></hr>
                    <div className="form-side-container">
                        <div className="form-side-contents">
                            <p style={{ fontWeight: 'bold', fontStyle: 'italic', textAlign: 'center' }}>AUDIENCE</p>

                            <div className="form-row">
                                <label htmlFor="targetAudience">Target Audience<span className="required">*</span></label>
                                <input className="basic-input-field" type="text" id="ta" placeholder="20-30 or 35-65" value={ta} readOnly></input>
                            </div>

                            <div className="form-row">
                                <label htmlFor="gender">Gender<span className="required">*</span></label>
                                <input className="basic-input-field" type="text" id="ta" placeholder="Male or Female or both" value={gender} readOnly></input>
                            </div>
                        </div>


                    </div>
                    <div className="space-padding"></div>
                    <hr className="sidebar-divider"></hr>
                    <div className="form-side-container">
                        <div className="form-side-contents">
                            <p style={{ fontWeight: 'bold', fontStyle: 'italic', textAlign: 'center' }}>THEME</p>
                            <div className="form-row">
                                <label htmlFor="seasonal">Seasonal</label>
                                <input className="basic-input-field" type="text" id="ta" placeholder="New Years or Chrsitmas.." value={seasonal} readOnly></input>
                            </div>

                            <div className="form-row">
                                <label htmlFor="seasonal">Regional</label>
                                <input className="basic-input-field" type="text" id="ta" placeholder="North America or Asia.." value={regional} readOnly></input>

                            </div>

                            <div className="form-row">
                                <label htmlFor="seasonal">Occasion (Restaurants)</label>
                                <input className="basic-input-field" type="text" id="ta" placeholder="Office Party or Birthday Party.." value={occasion} readOnly></input>

                            </div>
                        </div>

                    </div>
                    <div className="space-padding"></div>
                    <hr className="sidebar-divider"></hr>
                    <div className="form-side-container">
                        <div className="form-side-contents">
                            <p style={{ fontWeight: 'bold', fontStyle: 'italic', textAlign: 'center' }}>CONCEPT</p>
                            <div className="form-row">
                                <label htmlFor="description">Describe your creative<span className="required">*</span></label>
                                <input className="large-input-field" type="text" id="message" placeholder="Realistic painting of a dystopian industrial city..." value={message} readOnly></input>
                            </div>
                        </div>
                    </div>
                    <hr className="sidebar-divider"></hr>
                    <div className="form-side-container">
                        <div className="form-side-contents">
                            <p style={{ fontWeight: 'bold', fontStyle: 'italic', textAlign: 'center' }}>SPECIFICATION</p>
                            <div className="form-row">
                                <label htmlFor="contentType">Content Type</label>
                                <input className="basic-input-field" type="text" id="message" placeholder="Photo or Graphic..." value={contentType} readOnly></input>
                            </div>
                            <div className="form-row">
                                <label htmlFor="color">Color</label>
                                <input className="basic-input-field" type="text" id="message" placeholder="Warm or Cool..." value={color} readOnly></input>
                            </div>
                            <div className="form-row">
                                <label htmlFor="size">Size<span className="required">*</span></label>
                                <input className="basic-input-field" type="text" id="message" placeholder="1024x1024" value={size} readOnly></input>
                            </div>
                            <div className="form-row">
                                <label htmlFor="count">Image Count<span className="required">*</span></label>
                                <input className="basic-input-field" type="text" id="noi" placeholder="4 [maximum: 10]" value={noi} readOnly></input>
                            </div>
                        </div>
                    </div>

                </div>
                <div className="chat-container">
                    <div className="banner-header2">
                        <p>CREATIVE RECOMMENDATIONS</p> 
                        
                    </div>
                    <hr className="sidebar-divider"></hr>
                    
                        {load === '0' ? (
                            <Loading />
                        ) : load === '1' ? (
                            <div style={{
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                width: '100%',
                            }}>
                                <Loading />
                            </div>
                        ) : load === '2' && result !== null ? (
                            <GeneratedImages2 data={result.data}  onSelectedImagesCountChange={handleSelectedImagesCountChange}/>
                        ) : (
                            <h2 style={{ color: 'black' }}>Error while calling API</h2>
                        )
                        }

                   
                </div>
            </div>
        </main>
    );
}
