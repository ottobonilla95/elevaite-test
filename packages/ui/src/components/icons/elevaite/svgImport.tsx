import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGImport(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 20}
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M13.5 2.5c1.4 0 2.1 0 2.635.272a2.5 2.5 0 0 1 1.092 1.093C17.5 4.4 17.5 5.1 17.5 6.5v7c0 1.4 0 2.1-.273 2.635a2.5 2.5 0 0 1-1.092 1.092c-.535.273-1.235.273-2.635.273h-7c-1.4 0-2.1 0-2.635-.273a2.5 2.5 0 0 1-1.093-1.092C2.5 15.6 2.5 14.9 2.5 13.5M10 5v5m0 0H5m5 0L2.5 2.5"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
            />
        </svg>
    );
}
 
export default SVGImport;
