import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGArrowBack(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "#939393";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={12}
            width={24}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M22.5 6h-21m0 0 5 5m-5-5 5-5"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
            />
        </svg>
    );
}
 
export default SVGArrowBack;
