


// TYPES
/////////////

export function isObject(item: unknown): item is object {
    return Boolean(item) && item !== null && typeof item === "object";
}

export function isArrayOfStrings(data: unknown): data is string[] {
    if (!Array.isArray(data)) return false;
    for (const item of data) {
        if (typeof item !== "string") return false;
    }
    return true;
}


