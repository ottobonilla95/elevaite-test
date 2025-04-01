import React, { useEffect, useState } from 'react';
import path from 'path'

interface ImagePlaceholderProps {
    folderName:string;
    fileLocation: string;
}

const ImagePlaceholder: React.FC<ImagePlaceholderProps> = ({ folderName, fileLocation}) => {
    
    
    
    const imageFile = '/' + folderName + '/'  + fileLocation
    return (
        <div style={{ 
            width: '250px',
            height: '250px',
            border: '1px dashed black',
            alignItems: 'center'
        }}>
         <img className="img" src={imageFile} alt={imageFile} style={{ width: '100%', height: '100%'}} />

        </div>
    );
};

export default ImagePlaceholder;