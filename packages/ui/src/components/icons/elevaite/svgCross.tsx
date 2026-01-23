import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGCross({circled, ...props}: SVGProps<SVGSVGElement> & { size?: number, circled?: boolean }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;
    const defaultSize = circled ? 20 : 12;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : defaultSize}
            width={props.size ? props.size : defaultSize}
            viewBox={`0 0 ${defaultSize} ${defaultSize}`}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            {circled ? 
                <path
                    stroke={mainColor}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M10.001 6.666v6.667M6.668 9.999h6.667m5 0a8.333 8.333 0 1 1-16.667 0 8.333 8.333 0 0 1 16.667 0Z"
                />
            :
                <path
                    d="M6 1.333v9.333M1.335 6h9.333"
                    stroke={mainColor}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                />
            }
        </svg>
    );
}
 
export default SVGCross;
