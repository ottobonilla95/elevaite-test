import React from 'react';

interface ShoppingCartImagesProps {
    urls: string | string[] | undefined;
};

const ShoppingCartImages: React.FC<ShoppingCartImagesProps> = ({ urls }) => {
    // Ensure that urls is always an array, even if it's undefined
    const urlArray = Array.isArray(urls) ? urls : typeof urls === 'string' ? [urls] : [];

    return (
        <div className="sc-image-gallery-container">
            <div className="sc-image-gallery">
                {urlArray.map((url, index) => (
                    <div className="sc-image-item" key={index}>
                        <img className="sc-img" src={url} alt={`Image ${index}`} />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ShoppingCartImages;
