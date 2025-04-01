import React, { useState } from 'react';
import axios from 'axios';
import generatedImages from '../components/generatedImages';
import Image from 'next/image';

const ImageEditor: React.FC = () => {
    
    const [result, setResult] = useState<string | null>(null);
    const [urls, setUrls] = useState<string[]>([]);
    const handleButtonClick = async () => {
        try {
            const response = await axios.get('api/imageEditorApi');
            setResult(JSON.stringify(response.data, null, 2));
        } catch (error) {
            console.error('Error making API call:', error);
        }
    };
    
    const urlRegex = /https:\/\/[^\s]+/g;
    if(result !== null){
         const imgUrls = result.match(urlRegex);
         if(imgUrls != null){
            setUrls(imgUrls);
         }
         
        if (imgUrls) {
            console.log(imgUrls);
        } else {
            console.log('No URLs found in the string.');
        }
    }
    

    


    return (
    <div>
        <div className="uploadContainer2">
            <button onClick={handleButtonClick} className="button-align-right work-bench-button">
                <p>Generate</p>
            </button>
        </div>
        <div>
            <h2 style={{color: "white"}}>API Call Result:</h2>
            
            <pre style={{color: "white"}}>{result}</pre>
        </div>
    </div>
    );
};

export default ImageEditor;