import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGAddFile(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 19 22"
            width={props.size ? props.size : 19}
            height={props.size ? props.size * (22/19) : 22}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M17 9.5V5.8c0-1.68 0-2.52-.327-3.162a3 3 0 0 0-1.311-1.311C14.72 1 13.88 1 12.2 1H5.8c-1.68 0-2.52 0-3.162.327a3 3 0 0 0-1.311 1.311C1 3.28 1 4.12 1 5.8v10.4c0 1.68 0 2.52.327 3.162a3 3 0 0 0 1.311 1.311C3.28 21 4.12 21 5.8 21H9m2-11H5m2 4H5m8-8H5m10 14v-6m-3 3h6"
            />
        </svg>
    );
}
 
export default SVGAddFile;
