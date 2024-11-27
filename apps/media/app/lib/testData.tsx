import type { ChatMessageFileObject, ChatMessageObject, SessionObject } from "./interfaces";
import { ChatMessageFileTypes } from "./interfaces";

export function getTestSessionsList(amount: number): SessionObject[] {
    const list: SessionObject[] = [];
    for (let i=0; i<amount; i++) {
        list.push({
            id: `id_${i.toString()}`,
            label: `Session ${(i+1).toString()}`,
            messages: [],
            creationDate: new Date().toISOString(),
        })
    }
    return list;
}


export function getTestMessagesList(amount: number): ChatMessageObject[] {
    const list: ChatMessageObject[] = [];
    for (let i=0; i<amount; i++) {
        list.push({
            id: `id_${i.toString()}`,
            isBot: i % 2 !== 0,
            date: new Date().toISOString(),
            text: LOREM.slice(0, getRandomInRange(200, LOREM.length)),
            userName: "Test User",
            vote: getRandomInRange(-1, 1) as -1 | 0 | 1,
            files: getTestMessageFiles(),
        })
    }
    return list;
}


export function getTestMessageFiles(): ChatMessageFileObject[] {
    const files: ChatMessageFileObject[] = [];
    for (let i=0; i <= getRandomInRange(0, 6); i++) {
        files.push({
            id: `file_id_${(i+1).toString()}`,
            filename: `Test file ${(i+1).toString()}`,
            isViewable: getRandomInRange(0, 1) > 0,
            isDownloadable: getRandomInRange(0, 1) > 0,
            fileType: ChatMessageFileTypes.DOC,
        });
    }
    return files;
}

function getRandomInRange(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1) + min);
}

const LOREM = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec ut turpis est. Quisque dictum libero eu auctor tristique. Cras tincidunt blandit iaculis. Aliquam erat volutpat. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Vestibulum ac neque lacinia, maximus purus in, sodales neque. Nulla convallis aliquam sem, a iaculis augue porta vitae. Donec gravida magna ut odio egestas feugiat. Ut quis neque volutpat dui interdum fringilla. Pellentesque id tincidunt nulla. Suspendisse varius, turpis a commodo ultricies, urna elit faucibus nunc, a sollicitudin risus risus cursus nisi. Nulla sit amet magna faucibus mi dictum facilisis vitae ut eros.
In vel ultrices massa, et feugiat ex. Proin vel odio lorem. Nunc dignissim quam dolor, quis mollis dolor dignissim vitae. Morbi ut condimentum felis, at posuere massa. Sed aliquam elit dignissim, sagittis libero a, cursus tellus. Ut non placerat elit. Aliquam scelerisque urna a nunc ornare, eget dapibus dolor gravida. Phasellus rutrum venenatis bibendum.`

export function extractUniqueMediaData(markdown: string): { urls: string[]; names: string[] } {
    const urlsSet = new Set<string>();
    const namesSet = new Set<string>();

    // Regex to match thumbnail images specifically
    const imageRegex = /!\[(.*?)\]\(\s*(http[^\s)]+)\.thumbnail\.jpg\s*"(.*?)"\s*\)/g;

    let match: RegExpExecArray | null;

    // Loop through markdown to find all thumbnail image matches
    while ((match = imageRegex.exec(markdown)) !== null) {
        const altText: string = match[1].trim(); // Alt text for uniqueness
        const baseUrl: string = match[2].trim(); // Base URL without .thumbnail.jpg
        const title: string = match[3].trim(); // Title for namesSet

        // Get the filename and extension from alt text to construct the full URL
        const filename: string = altText.split('/').pop() || ''; // Extract the filename
        const extension = filename.split('.').pop(); // Extract the extension

        // Determine the full URL, replacing `.thumbnail.jpg` with `.jpg` for the original image
        const url: string = extension ? `${baseUrl}.${extension}` : `${baseUrl}.jpg`; // Full URL

        // Create a unique key using both title and alt text for uniqueness
        const uniqueKey = `${title}|${altText}`; 

        // Add to the sets only if the combination is unique
        if (!namesSet.has(uniqueKey)) {
            namesSet.add(uniqueKey); // Add unique key to namesSet
            urlsSet.add(url); // Add unique URL to urlsSet
        }

        console.log("Title:", title, "URL:", url);
    }

    // Regex to capture **only non-thumbnail** images (without .thumbnail.jpg suffix)
    const nonThumbnailImageRegex = /!\[(.*?)\]\(\s*(http[^\s)]+)(?!\.thumbnail\.jpg)(.*?)\)/g;

    // Loop through markdown to find non-thumbnail images and exclude thumbnail ones
    while ((match = nonThumbnailImageRegex.exec(markdown)) !== null) {
        const altText: string = match[1].trim(); // Alt text for uniqueness
        const baseUrl: string = match[2].trim(); // Full URL (no thumbnail)
        const title: string = match[3].trim(); // Title for namesSet

        // Avoid adding if it's mistakenly treated as a thumbnail
        if (baseUrl.includes('.thumbnail.jpg')) {
            continue; // Skip any URLs that end with .thumbnail.jpg
        }

        const uniqueKey = `${title}|${altText}`; // Use both title and alt text for uniqueness

        // Add to the sets only if the combination is unique
        if (!namesSet.has(uniqueKey)) {
            namesSet.add(uniqueKey); // Add unique key to namesSet
            urlsSet.add(baseUrl); // Add the full URL directly to urlsSet
        }

        console.log("Title:", title, "URL:", baseUrl);
    }

    // Return the unique URLs and names as arrays
    return {
        urls: Array.from(urlsSet),
        names: Array.from(namesSet),
    };
}

// export function extractUniqueMediaData(markdown: string): { urls: string[]; names: string[] } {
//     const urlsSet = new Set<string>();
//     const namesSet = new Set<string>();
    
//     // Regex to match image markdown format and capture alt text and title
//     const imageRegex = /!\[(.*?)\]\(\s*(http[^\s)]+)\.thumbnail\.jpg\s*"(.*?)"\s*\)/g;

//     let match: RegExpExecArray | null;

//     while ((match = imageRegex.exec(markdown)) !== null) {
//         const altText: string = match[1].trim(); // Alt text for uniqueness
//         const baseUrl: string = match[2].trim(); // Base URL without .thumbnail.jpg
//         const title: string = match[3].trim(); // Title for namesSet
//         const filename: string = altText.split('/').pop() || ''; // Get the filename from alt text
//         const extension = filename.split('.').pop(); // Extract the extension
        
//         const url: string = extension ? `${baseUrl}.${extension}` : `${baseUrl}.jpg`; // Full URL
//         const uniqueKey = `${title}|${altText}`; // Use a separator to ensure uniqueness

//         if (!namesSet.has(uniqueKey)) {
//             namesSet.add(uniqueKey); // Add unique key
//             urlsSet.add(url); // Add unique URL only if the title is added
//         }
//         console.log("Title:", title, "URL:", url);
//     }
//     const nonThumbnailImageRegex = /!\[(.*?)\]\(\s*(http[^\s)]+)(?!\.thumbnail\.jpg)(.*?)\)/g;

//     while ((match = nonThumbnailImageRegex.exec(markdown)) !== null) {
//       const altText: string = match[1].trim(); // Alt text for uniqueness
//       const baseUrl: string = match[2].trim(); // Full URL (no need to strip anything)
//       const title: string = match[3].trim(); // Title for namesSet
//       const uniqueKey = `${title}|${altText}`; // Use a separator to ensure uniqueness
//       // Add URL and name only if unique (no changes needed to the URL)
//       if (!namesSet.has(uniqueKey)) {
//         namesSet.add(uniqueKey); // Add unique key
//         urlsSet.add(baseUrl); // Add the full URL directly
//       }
//       console.log("Title:", title, "URL:", baseUrl);
//     }

//     return {
//         urls: Array.from(urlsSet),
//         names: Array.from(namesSet),
//     };
// }