import Header from '@/components/header';
import { useRouter } from 'next/router';
import React, { useState, useEffect } from 'react';
import Loading from '@/components/loading';
import GeneratedImages2 from '@/components/generatedImages2';
import axios from 'axios';
import { FaArrowLeft, FaSignOutAlt, FaShoppingCart } from 'react-icons/fa';
import { useSession, signOut } from 'next-auth/react';

interface ImageData {
    url: string;
}

interface ApiResponse {
    created: number;
    data: ImageData[];
}

type DataItem = {
    url: string;
};

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
    const stringifiedQuery = {
        gender: gender?.toString() || '',
        seasonal: seasonal?.toString() || '',
        regional: regional?.toString() || '',
        occasion: occasion?.toString() || '',
        contentType: contentType?.toString() || '',
        color: color?.toString() || '',
        size: size?.toString() || '',
    };

    //const [urlsArray, setUrlsArray] = useState([]);

    const [ta, setTa] = useState(targetAudience);
    const [message, setMessage] = useState(description);
    const [noi, setNoi] = useState(imageCount);
    const [load, setLoad] = useState(loading);
    const [result, setResult] = useState<ApiResponse | null>();
    const [selectedContentType, setContentType] = useState<string | null>(stringifiedQuery.contentType);
    const [selectedGenderValue, setSelectedGenderValue] = useState<string | null>(stringifiedQuery.gender);
    const [selectedSeasonalValue, setSelectedSeasonalValue] = useState<string | null>(stringifiedQuery.seasonal);
    const [selectedRegionalValue, setSelectedRegionalValue] = useState<string | null>(stringifiedQuery.regional);
    const [selectedOccasionValue, setSelectedOccasionValue] = useState<string | null>(stringifiedQuery.occasion);
    const [selectedColor, setColor] = useState<string | null>(stringifiedQuery.color);
    const [selectedSizeValue, setSelectedSizeValue] = useState<string | null>(stringifiedQuery.size);
    const { data: session } = useSession();
    const userName = session?.user?.email?.split("@")[0];


    const [selectedImagesCount, setSelectedImagesCount] = useState(0);
    const [selectedImageUrl, setSelectedImageUrl] = useState<string[]>([]);
    const handleSelectedImagesCountChange = (count: number, selectedUrls: string[]) => {
        setSelectedImagesCount(count);
        setSelectedImageUrl(selectedUrls);
    }
    /* const handleContentTypeonClick = (value: string) => {
         setContentType(value);
     };
 
 
     const handleGenderClick = (value: string) => {
         setSelectedGenderValue(value);
     };*/

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

    const handleBackClick = () => {
        router.push('/homepage');
    };

    const handleShoppingCartClick = async () => {
        let urlsArray: string[] =[];
        if (result !== null && result !== undefined){
             urlsArray = result.data.map(item => item.url);
        }

        //create Creative Brief record
        const response = await axios.get('http://localhost:3000/api/createCreativeBrief', {
            params: {
                targetAudience: targetAudience as string,
                gender: stringifiedQuery.gender as string,
                seasional: stringifiedQuery.seasonal as string,
                regional: stringifiedQuery.regional as string,
                occasion: stringifiedQuery.occasion as string,
                creativeDescription: description as string,
                contentType: stringifiedQuery.contentType as string,
                color: stringifiedQuery.color as string,
                size: stringifiedQuery.size as string,
                imageCount: imageCount as string,
                urlList: urlsArray.join(","),
                offeringMsg: "",
                cta: "",
                ea: "",
                pFileUrl: "",
                bFileUrl: "",
                selectedUrlList: "",
                userName: userName as string

            }
        });
        console.log(response.data);

        const formData = {
          url: selectedImageUrl,
          count: selectedImagesCount,
          cbID: response.data.ID
        };
    
        router.push({
          pathname: '/shoppingCart',
          query: formData
        });
    };

    const handleSignOut = async () => {
        await signOut({ callbackUrl: "/login" });
    };

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
                console.log("Response data: ", response.data);
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

            <div className="frame-2">
                <div className="frame-3">
                    <img
                        className="frame-1000004664"
                        src="img/frame-1000004664.svg"
                        alt="Frame 1000004664"
                    />
                    <img className="line-1 line" src="img/line-1.svg" alt="Line 1" />
                    <div className="product-support">Campaign Creatives Management</div>
                </div>

                <div className="frame-2-1">

                    <button
                        style={{ width: "25px", height: "25px", position: "relative" }}
                        onClick={handleShoppingCartClick}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 576 512"
                            fill="currentColor"
                        >
                            <path d="M96 0C107.5 0 117.4 8.19 119.6 19.51L121.1 32H541.8C562.1 32 578.3 52.25 572.6 72.66L518.6 264.7C514.7 278.5 502.1 288 487.8 288H170.7L179.9 336H488C501.3 336 512 346.7 512 360C512 373.3 501.3 384 488 384H159.1C148.5 384 138.6 375.8 136.4 364.5L76.14 48H24C10.75 48 0 37.25 0 24C0 10.75 10.75 0 24 0H96zM128 464C128 437.5 149.5 416 176 416C202.5 416 224 437.5 224 464C224 490.5 202.5 512 176 512C149.5 512 128 490.5 128 464zM512 464C512 490.5 490.5 512 464 512C437.5 512 416 490.5 416 464C416 437.5 437.5 416 464 416C490.5 416 512 437.5 512 464z" />
                        </svg>

                        {selectedImagesCount > 0 &&
                            (<div
                                style={{
                                    color: "white",
                                    width: "10px",
                                    height: "1.5rem",
                                    position: "absolute",
                                    bottom: 0,
                                    right: 0,
                                    transform: "translate(25%, 25%)",
                                }}
                            >
                                {selectedImagesCount}
                            </div>)}
                    </button>

                    <div className="name">{session?.user?.name}</div>

                    <button onClick={handleSignOut} className="logout-button">
                        <FaSignOutAlt height="14px" width="14px" color="white" />
                    </button>
                </div>
            </div>
            <div className="app-container">
                <div className="sidebar-container2">
                    <div className="config-container">
                        <FaArrowLeft className="left-arrow" onClick={handleBackClick} />

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
                        <GeneratedImages2 data={result?.data || []} onSelectedImagesCountChange={handleSelectedImagesCountChange} />
                    ) : (
                        <h2 style={{ color: 'black' }}>Error while calling API</h2>
                    )
                    }


                </div>
            </div>
        </main>
    );
}
