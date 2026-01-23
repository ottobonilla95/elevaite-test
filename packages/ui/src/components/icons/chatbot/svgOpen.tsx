import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGOpen(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 14 14"
            width={props.size ? props.size : 14}
            height={props.size ? props.size : 14}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M13 5V1m0 0H9m4 0L7.667 6.333m-2-4H4.2c-1.12 0-1.68 0-2.108.218a2 2 0 0 0-.874.874C1 3.853 1 4.413 1 5.533V9.8c0 1.12 0 1.68.218 2.108a2 2 0 0 0 .874.874C2.52 13 3.08 13 4.2 13h4.267c1.12 0 1.68 0 2.108-.218a2 2 0 0 0 .874-.874c.218-.428.218-.988.218-2.108V8.333"
            />
        </svg>
    );
}
 
export default SVGOpen;
