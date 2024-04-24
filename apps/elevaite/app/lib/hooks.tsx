import { useEffect } from "react"




export function useAutosizeTextArea(textAreaRef: HTMLTextAreaElement | null, value: string): void {
    useEffect(() => {
        if (!textAreaRef) return;
        // Reset the height to get correct scrollHeight
        textAreaRef.style.height = "0px";
        const { scrollHeight } = textAreaRef;  
        // Set the height directly
        textAreaRef.style.height = `${scrollHeight.toString()}px`
    }, [textAreaRef, value])
  }












