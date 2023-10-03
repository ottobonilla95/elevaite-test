import React from 'react';
import GeneratedImages2 from '../components/generatedImages2';

const jsonData = {
    "created": 1693939500,
    "data": [
      {
        "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/org-j6FfmQXGihZhL5cXBSZYm5NH/user-sk7Qyc5sz8fWsHhvK42SuG0H/img-1zFxkSbEmL7obI0LQbi4Rzyx.png?st=2023-09-05T17%3A44%3A59Z&se=2023-09-05T19%3A44%3A59Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-09-04T19%3A23%3A21Z&ske=2023-09-05T19%3A23%3A21Z&sks=b&skv=2021-08-06&sig=Fre7I6KTIaNlGQOrl6gU0KiD/a5EBqvl%2B7zgm%2BRxrL4%3D"
      },
      {
        "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/org-j6FfmQXGihZhL5cXBSZYm5NH/user-sk7Qyc5sz8fWsHhvK42SuG0H/img-UatpVILmkJ3cc2TBvs72KLGc.png?st=2023-09-05T17%3A45%3A00Z&se=2023-09-05T19%3A45%3A00Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-09-04T19%3A23%3A21Z&ske=2023-09-05T19%3A23%3A21Z&sks=b&skv=2021-08-06&sig=ii0NtVUxnFGyKo987XoSChOanl0XjbInwfaJYHK5pqA%3D"
      },
      {
        "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/org-j6FfmQXGihZhL5cXBSZYm5NH/user-sk7Qyc5sz8fWsHhvK42SuG0H/img-ChaSjsf8L6QO180ZOXMwOYpb.png?st=2023-09-05T17%3A45%3A00Z&se=2023-09-05T19%3A45%3A00Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-09-04T19%3A23%3A21Z&ske=2023-09-05T19%3A23%3A21Z&sks=b&skv=2021-08-06&sig=UMFJpYeXNPxNDDr3worcVhgQQpNOcXshJeFdgLUsx7w%3D"
      }
    ]
  };

function App() {
  return (
    <div>
      <GeneratedImages2 data={jsonData.data} />
    </div>
  );
}

export default App;
