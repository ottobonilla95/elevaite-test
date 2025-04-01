//NOT USED

import React from 'react';

interface ImageGalleryProps {
    onSelectedImage: (imageName: string) => void;
}

const template: React.FC<ImageGalleryProps> = ({ onSelectedImage }) => {

    const imageFileName  = ['banner-88x31px.png', 'banner-120x24px.png', 'banner-120x90px.png', 'banner-120x600px.png', 'banner-125x125px.png', 'banner-160x600px.png', 'banner-180x150px.png', 'banner-234x60px.png', 'banner-240x400px.png','banner-250x250px.png', 'banner-300x250px.png'];

  return (
    <div className="templates-gallery">
        {imageFileName.map((filename) => (
        <img
            key={filename}
            src={`/templates/${filename}`}
            alt={filename}
            onClick={() => onSelectedImage(filename)}
        />      
        ))}
    </div>
  )
}

export default template