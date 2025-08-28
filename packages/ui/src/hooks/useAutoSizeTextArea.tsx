import { useEffect } from "react";



export function useAutoSizeTextArea(textAreaRef: HTMLTextAreaElement | null, value: string, maxRows?: number): void {
    useEffect(() => {
        if (!textAreaRef) return;
        // Reset the height to get correct scrollHeight
        textAreaRef.style.height = "0px";

        // If maxRows is not provided, preserve original behavior 1:1
        if (typeof maxRows !== "number" || !isFinite(maxRows)) {
            const { scrollHeight } = textAreaRef;
            textAreaRef.style.height = `${scrollHeight.toString()}px`;
            textAreaRef.style.overflowY = "hidden";
            return;
        }

        // With maxRows: cap height and toggle overflow
        const cs = window.getComputedStyle(textAreaRef);
        const lineHeight = parseFloat(cs.lineHeight || "0") || 20;
        const maxHeight = lineHeight * maxRows;
        const sh = textAreaRef.scrollHeight;

        textAreaRef.style.height = `${Math.min(sh, maxHeight).toString()}px`;
        textAreaRef.style.overflowY = sh > maxHeight ? "auto" : "hidden";
    }, [textAreaRef, value, maxRows])
}