import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGClose(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 10 10"
            width={props.size ? props.size : 10}
            height={props.size ? props.size : 10}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.333}
                d="M9 1 1 9m0-8 8 8"
            />
        </svg>
    );
}
 
export default SVGClose;
