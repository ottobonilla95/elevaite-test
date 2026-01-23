import { useLayoutEffect } from "react";
import { useConfigPanel } from "../contexts/ConfigPanelContext";


const SCROLL_CONTAINER_SELECTOR = ".inner-config";


export function useFocusAnchor(): void {
    const { focusAnchor, clearFocusAnchor } = useConfigPanel();

    useLayoutEffect(() => {
        if (!focusAnchor) return;

        const element = document.getElementById(focusAnchor);
        const scrollContainer = document.querySelector(SCROLL_CONTAINER_SELECTOR);
        
        if (element && scrollContainer) {
            const containerRect = scrollContainer.getBoundingClientRect();
            const elementRect = element.getBoundingClientRect();
            
            const currentScroll = scrollContainer.scrollTop;
            const elementOffset = elementRect.top - containerRect.top + currentScroll;
            
            const containerHeight = scrollContainer.clientHeight;
            const elementHeight = element.offsetHeight;
            
            // If element is taller than container, align to top; otherwise center it
            const targetScroll = elementHeight >= containerHeight
                ? elementOffset
                : elementOffset - (containerHeight / 2) + (elementHeight / 2);
            
            scrollContainer.scrollTop = Math.max(0, targetScroll);
        }

        clearFocusAnchor();
    }, [focusAnchor, clearFocusAnchor]);
}
