import type { ChatMessageResponse, SessionSummaryObject } from "./interfaces";







export function isChatMessageResponse(data: unknown): data is ChatMessageResponse {
    return isChatMessageResponseObject(data);
}

export function isSessionSummaryResponse(data: unknown): data is SessionSummaryObject {
    return isSessionSummaryObject(data);
}



// OBJECTS
///////////



function isObject(item: unknown): item is object {
    return Boolean(item) && item !== null && typeof item === "object";
}


function isChatMessageResponseObject(item: unknown): item is ChatMessageResponse {
    return isObject(item) &&
        "text" in item &&
        "refs" in item &&
        Array.isArray(item.refs);
}

function isSessionSummaryObject(item: unknown): item is SessionSummaryObject {
    return isObject(item) &&
        "title" in item &&
        "problem" in item &&
        "solution" in item;
}

