import React from 'react';

interface ShoppingCartImagesProps {
    urls: string[];
};

const ShoppingCartImages: React.FC<ShoppingCartImagesProps> = ({ urls }) => {

    return(
        <div className="sc-image-gallery-container">
            <div className="sc-image-gallery">
                {urls.map((url, index) => (
                    <div className="sc-image-item" key ={index}>
                        <img className="sc-img" src={url} alt={`Image ${index}`} />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ShoppingCartImages;