import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGXmark(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 14}
            viewBox="0 0 14 14"
            width={props.size ? props.size : 14}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M13 1 1 13M1 1l12 12"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
            />
        </svg>
    );
}
 
export default SVGXmark;