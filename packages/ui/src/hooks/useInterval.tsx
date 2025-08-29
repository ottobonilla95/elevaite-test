"use client";
import { useEffect, useRef } from "react";



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