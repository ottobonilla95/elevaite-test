import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGActionRefresh(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 15 14"
            width={props.size ? props.size * (15/14) : 15}
            height={props.size ? props.size : 14}
            {...props}
        >
            <path
                fill={mainColor}
                d="M10.773 3.23a5.333 5.333 0 1 0 1.352 5.252.667.667 0 0 1 1.281.37 6.667 6.667 0 1 1-1.69-6.564c.424.424.88.95 1.284 1.442V1.667a.667.667 0 0 1 1.333 0v4a.667.667 0 0 1-.666.666h-4a.667.667 0 0 1 0-1.333h2.646c-.456-.572-1.03-1.26-1.54-1.77Z"
            />
        </svg>
    );
}
 
export default SVGActionRefresh;
