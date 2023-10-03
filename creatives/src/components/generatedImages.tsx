//NOT USED!!
import React from 'react';

interface generatedImagesProps {
  data: { url: string }[];
}

const generatedImages: React.FC<generatedImagesProps> = ({ data }) => {
  return (
    <div style={{ border: '2px solid orange', padding: '10px', overflowX: 'auto' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {data.map((item, index) => (
          <div key={index} style={{ width: 'calc(50% - 20px)' }}>
            <img src={item.url} alt={`Image ${index}`} style={{ maxWidth: '100%', marginBottom: '10px' }} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default generatedImages;
