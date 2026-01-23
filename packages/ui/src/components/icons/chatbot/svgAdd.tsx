import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGAdd(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    // let mainColor = "currentColor";
    let mainColor = "var(--ev-colors-text)";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            height={props.size ? props.size : 20}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M10.001 6.666v6.667M6.668 9.999h6.667m5 0a8.333 8.333 0 1 1-16.667 0 8.333 8.333 0 0 1 16.667 0Z"
            />
        </svg>
    );
}
 
export default SVGAdd;
