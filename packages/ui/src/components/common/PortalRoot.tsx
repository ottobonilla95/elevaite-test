"use client";
import type { JSX } from "react";
import { useEffect, useRef } from "react";


declare global {
    interface Window {
        __PORTAL_ROOT__?: HTMLElement;
    }
}


//Container for all portaled elements (menus, tooltips, etc.)
// This should be mounted once at the root
export function PortalRoot(): JSX.Element {
    const portalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Store reference globally so hooks can access it
        if (portalRef.current) {
            window.__PORTAL_ROOT__ = portalRef.current;
        }
        
        return () => {
            delete window.__PORTAL_ROOT__;
        };
    }, []);

    return (
        <div 
            ref={portalRef}
            id="portal-root" 
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                pointerEvents: "none",
                zIndex: 9999,
            }}
        />
    );
}


export function getPortalRoot(): HTMLElement | null {
    const globalRoot = window.__PORTAL_ROOT__;
    if (globalRoot) return globalRoot;    
    return document.getElementById("portal-root");
}
