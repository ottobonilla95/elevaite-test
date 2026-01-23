import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGSelectionArrow(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 6 8"
            width={props.size ? props.size : 6}
            height={props.size ? props.size * (8 / 6) : 8}
            {...props}
        >
            <path
                fill={mainColor}
                stroke={mainColor}
                d="M4.758 4.384a.5.5 0 0 0 0-.768L1.32.75a.5.5 0 0 0-.82.384v5.73a.5.5 0 0 0 .82.384l3.438-2.865Z"
            />
        </svg>
    );
}
 
export default SVGSelectionArrow;
