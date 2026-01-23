"use client";
import { useEffect, useRef } from "react";


type HTMLElementRef = React.MutableRefObject<HTMLElement | null>;

function useOutsideDetector(
    ref: HTMLElementRef,
    onOutsideClick: (event: MouseEvent) => void,
    options: {
        isDisabled?: boolean;
        ignoredRefs?: HTMLElementRef[];
        useAltHandling?: boolean;
    }
): void {

    useEffect(() => {
        if (options.isDisabled) return;

        function isInsideAnyRef(target: Node | null, refs?: HTMLElementRef[]): boolean {
            if (!target || !refs || refs.length === 0) return false;
            return refs.some((ignoredRef) => ignoredRef.current?.contains(target));
        }

        function handlePointerDown(event: PointerEvent): void {
            const target = event.target as Node | null;

            if (!ref.current || !target) return;
            if (ref.current.contains(target)) return;

            if (isInsideAnyRef(target, options.ignoredRefs)) return;
            onOutsideClick(event);
        }

        function handleMouseUp(event: MouseEvent): void {
            const target = event.target as Node | null;

            if (!ref.current || !target) return;

            if (!ref.current.contains(target)) {
                if (isInsideAnyRef(target, options.ignoredRefs)) {
                    return;
                }
                onOutsideClick(event);
            }
        }


        if (options.useAltHandling) {
            document.addEventListener("pointerdown", handlePointerDown, true);
            return () => {
                document.removeEventListener("pointerdown", handlePointerDown, true);
            };
        } 
        // Else
        document.addEventListener("mouseup", handleMouseUp);
        return () => {
            document.removeEventListener("mouseup", handleMouseUp);
        };        

    }, [ref, options]);
}

interface ClickOutsideDetectorProps {
    onOutsideClick: (event: MouseEvent) => void;
    children?: React.ReactNode;
    disabled?: boolean;
    ignoredRefs?: HTMLElementRef[];
    useAltHandling?: boolean;
}

export function ClickOutsideDetector(props: ClickOutsideDetectorProps): React.ReactElement {
    const wrapperRef = useRef<HTMLElement | null>(null);
    useOutsideDetector(
        wrapperRef,
        props.onOutsideClick,
        {
            isDisabled: props.disabled,
            ignoredRefs: props.ignoredRefs,
            useAltHandling: props.useAltHandling,
        }
    );

    return (
        <section ref={wrapperRef} style={{ display: "contents" }}>
            {props.children}
        </section>
    );
}
