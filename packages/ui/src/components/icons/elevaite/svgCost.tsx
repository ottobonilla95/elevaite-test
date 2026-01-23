import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGCost(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 25 20"
            width={props.size ? props.size * (25 / 20) : 25}
            height={props.size ? props.size : 20}
            {...props}
        >
            <path
                fill={mainColor}
                d="M22.272.332h-19.2a2.382 2.382 0 0 0-2.388 2.4l-.012 14.4c0 1.332 1.068 2.4 2.4 2.4h19.2c1.332 0 2.4-1.068 2.4-2.4v-14.4c0-1.332-1.068-2.4-2.4-2.4Zm-9.6 7.2h-4.8v1.2h3.6c.66 0 1.2.54 1.2 1.2v3.6c0 .66-.54 1.2-1.2 1.2h-1.2v1.2h-2.4v-1.2h-2.4v-2.4h4.8v-1.2h-3.6c-.66 0-1.2-.54-1.2-1.2v-3.6c0-.66.54-1.2 1.2-1.2h1.2v-1.2h2.4v1.2h2.4v2.4Zm4.8 7.5-2.4-2.4h4.8l-2.4 2.4Zm-2.4-7.5 2.4-2.4 2.4 2.4h-4.8Z"
            />
        </svg>
    );
}
 
export default SVGCost;
