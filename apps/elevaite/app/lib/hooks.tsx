import { useEffect, useRef } from "react";




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


export function useInterval(callback: () => void, delay: number): void {
    const savedCallback = useRef<() => void>();      
    // Remember the latest callback.
    useEffect(() => {
        savedCallback.current = callback;
    }, [callback]);
  
    // Set up the interval.
    useEffect(() => {
        function tick(): void {
            if (savedCallback.current) {
                savedCallback.current();
            }
        }
      const intervalId = setInterval(tick, delay);
      return () => { clearInterval(intervalId); };
    }, [delay]);
}


