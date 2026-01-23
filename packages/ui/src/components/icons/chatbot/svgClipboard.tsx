import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGClipboard(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 18 21"
            width={props.size ? props.size : 18}
            height={props.size ? props.size * (21/18) : 21}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12.5 3H15a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h2.5"
            />
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5.621 2.515A2 2 0 0 1 7.561 1h2.877a2 2 0 0 1 1.94 1.515L13 5H5l.621-2.485Z"
            />
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeWidth={2}
                d="M6 11h6m-6 4h6"
            />
        </svg>
    );
}
 
export default SVGClipboard;
