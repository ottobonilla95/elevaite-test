import React, { useState, useEffect } from 'react';
import { FaDownload } from 'react-icons/fa';

interface GeneratedImagesProps {
  data: { url: string | null }[];
  onSelectedImagesCountChange: (count: number, selectedImageUrls: string[]) => void;
}

const GeneratedImages2: React.FC<GeneratedImagesProps> = ({ data, onSelectedImagesCountChange }) => {
  const [selectedImages, setSelectedImages] = useState<number[]>([]);
  const [selectedImageUrls, setSelectedImageUrls] = useState<string[]>([]);

  useEffect(() => {
    onSelectedImagesCountChange(selectedImages.length, selectedImageUrls);
  }, [selectedImages, selectedImageUrls, onSelectedImagesCountChange]);

  const handleDownload = (url: string | null, index: number) => {
    if (url) {
      const link = document.createElement('a');
      link.href = url;
      link.download = `DalleImage_${index + 1}.png`;
      link.dispatchEvent(new MouseEvent('click'));
      link.remove();
    }
  };

  const toggleImageSelection = (index: number, url:string | null) => {
    
    if (selectedImages.includes(index)) {
      setSelectedImages(selectedImages.filter((i) => i !== index));
      setSelectedImageUrls(selectedImageUrls.filter((u) => u !== url));
    } else {
      setSelectedImages([...selectedImages, index]);
      setSelectedImageUrls([...selectedImageUrls, url || '']);
    }
  };

  return (
    <div>
    <div className="gallery-container">
      {data.map((item, index) => (
        <div
          className={`gallery-item ${selectedImages.includes(index) ? 'selected' : ''}`}
          key={index}
          
        >
          {item.url ? (
            <div className="image-container" onClick={() => toggleImageSelection(index, item.url)}>
              <img src={item.url} alt={`Image ${index}`} className="image" />
            </div>
          ) : (
            <p>Error: URL is null</p>
          )}
        </div>
      ))}
    </div>
    </div>
  );
};

export default GeneratedImages2;
