import { ChatMessageFileObject, ChatMessageFileTypes, ChatMessageObject, SessionListItem } from "./interfaces";








export function getTestSessionsList(amount: number): SessionListItem[] {
    const list: SessionListItem[] = [];
    for (var i=0; i<amount; i++) {
        list.push({
            id: "id_" + i,
            label: "Firmware Upgrade " + i,
        })
    }
    return list;
}




export function getTestMessagesList(amount: number): ChatMessageObject[] {
    const list: ChatMessageObject[] = [];
    for (var i=0; i<amount; i++) {
        list.push({
            id: "id_" + i,
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
    for (var i=0; i <= getRandomInRange(0, 6); i++) {
        files.push({
            id: "file_id_" + (i+1),
            filename: "Test file " + (i+1),
            isViewable: getRandomInRange(0, 1) > 0,
            isDownloadable: getRandomInRange(0, 1) > 0,
            fileType: ChatMessageFileTypes.DOC,
        });
    }
    return files;
}




function getRandomInRange(min: number, max: number) {
    return Math.floor(Math.random() * (max - min + 1) + min);
}

const LOREM = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec ut turpis est. Quisque dictum libero eu auctor tristique. Cras tincidunt blandit iaculis. Aliquam erat volutpat. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Vestibulum ac neque lacinia, maximus purus in, sodales neque. Nulla convallis aliquam sem, a iaculis augue porta vitae. Donec gravida magna ut odio egestas feugiat. Ut quis neque volutpat dui interdum fringilla. Pellentesque id tincidunt nulla. Suspendisse varius, turpis a commodo ultricies, urna elit faucibus nunc, a sollicitudin risus risus cursus nisi. Nulla sit amet magna faucibus mi dictum facilisis vitae ut eros.
In vel ultrices massa, et feugiat ex. Proin vel odio lorem. Nunc dignissim quam dolor, quis mollis dolor dignissim vitae. Morbi ut condimentum felis, at posuere massa. Sed aliquam elit dignissim, sagittis libero a, cursus tellus. Ut non placerat elit. Aliquam scelerisque urna a nunc ornare, eget dapibus dolor gravida. Phasellus rutrum venenatis bibendum.`
