//NOT USED
import React, { useEffect, useState } from 'react';

interface ImageGalleryProps {
    onImageSelect: (imageName: string) => void;
    fileLocation: string;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ onImageSelect , fileLocation}) => {
    const [imageUrls, setImageUrls] = useState<string[]>([]);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);

    useEffect(() => {
        async function fetchImageUrls() {
            try {
                const response = await fetch('/api/images?fileLocation=' + fileLocation);
                const data = await response.json();
                setImageUrls(data.imageUrls);
            } catch (error) {
                console.error('Error fetching image URLs:', error);
            }
        }
        
        fetchImageUrls();
    }, []);
    

    const handleImageClick = (imageUrl: string) => {
        const imageName = imageUrl.substring(imageUrl.lastIndexOf('/') + 1);
        setSelectedImage(imageName);
        onImageSelect(imageName);
    }
    return (
    <div>
        {imageUrls.map((imageUrl, index) => (
        <img className="img"
        key={index}
        src={imageUrl}
        alt={`Image ${index}`}
        onClick={() => handleImageClick(imageUrl)}
       />
       ))}
    </div>
    );
};

export default ImageGallery;