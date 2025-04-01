//NOT USED
import React from 'react';

const gen: React.FC = () => {
  const urls: string[] = [
    "https://oaidalleapiprodscus.blob.core.windows.net/private/org-j6FfmQXGihZhL5cXBSZYm5NH/user-sk7Qyc5sz8fWsHhvK42SuG0H/img-w0OqJ2NEl1QBta6fvfmwAkz2.png?st=2023-09-04T15%3A46%3A14Z&se=2023-09-04T17%3A46%3A14Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-09-04T06%3A09%3A30Z&ske=2023-09-05T06%3A09%3A30Z&sks=b&skv=2021-08-06&sig=uaCy3cIluLV35gkZbYuwjjEKGZ82qS8kZyyI0lR3zkY%3D",
    "https://oaidalleapiprodscus.blob.core.windows.net/private/org-j6FfmQXGihZhL5cXBSZYm5NH/user-sk7Qyc5sz8fWsHhvK42SuG0H/img-SZtVj8dBen6Ak53OMtYB4sjj.png?st=2023-09-04T15%3A46%3A13Z&se=2023-09-04T17%3A46%3A13Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-09-04T06%3A09%3A30Z&ske=2023-09-05T06%3A09%3A30Z&sks=b&skv=2021-08-06&sig=XvbvN03hJB8lVhBFnZf40BU4pxoTKg04Hz902FC49As%3D"
  ];

  return (
    <div className="gallery-container">
      {urls.map((url, index) => (
        <div className="gallery-item" key={index}>
          <img src={url} alt={`Image ${index}`} />
        </div>
      ))}
    </div>
  );
};

export default gen;
