import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGFolder(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 19 16"
            width={props.size ? props.size * (19/16) : 19}
            height={props.size ? props.size : 16}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.257}
                d="M1 7.162V1.8c0-.277.225-.502.503-.502H6.68c.12 0 .236.043.327.12l2.65 2.272a.503.503 0 0 0 .327.121h7.272c.277 0 .503.225.503.503v2.85M1 7.162V14.2c0 .277.225.502.503.502h15.753a.503.503 0 0 0 .503-.502V7.162M1 7.162h16.759"
            />
        </svg>
    );
}
 
export default SVGFolder;
