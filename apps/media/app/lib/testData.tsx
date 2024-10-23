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

    // Regex to match image markdown format and capture alt text and title
    const imageRegex = /!\[(.*?)\]\((http[^)]+)\.thumbnail\.jpg\s*"(.*?)"\)/g;

    let match: RegExpExecArray | null;

    while ((match = imageRegex.exec(markdown)) !== null) {
        const altText: string = match[1].trim(); // Alt text for uniqueness
        const baseUrl: string = match[2].trim(); // Base URL without extension
        const title: string = match[3].trim(); // Title for namesSet
        const filename: string = altText.split('/').pop() || ''; // Get the filename from alt text
        const extension = filename.split('.').pop(); // Extract the extension
        
        const url: string = extension ? `${baseUrl}.${extension}` : `${baseUrl}.jpg`; // Full URL with correct extension
        
        // Add unique title based on alt text
        if (!namesSet.has(title)) {
            namesSet.add(title); // Add unique title
            urlsSet.add(url); // Add unique URL only if the title is added
        }
    }

    return {
        urls: Array.from(urlsSet),
        names: Array.from(namesSet),
    };
}