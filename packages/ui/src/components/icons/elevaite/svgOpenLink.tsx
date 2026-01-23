import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGOpenLink(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 16 16"
            height={props.size ? props.size : 16}
            width={props.size ? props.size : 16}
            {...props}
        >
            <path
                fill={mainColor}
                d="M14.188.969h-9a.844.844 0 0 0-.844.844v2.53H1.812a.844.844 0 0 0-.843.845v9a.844.844 0 0 0 .844.843h9a.843.843 0 0 0 .843-.844v-2.53h2.531a.843.843 0 0 0 .844-.845v-9a.843.843 0 0 0-.844-.843Zm-4.22 12.375H2.657V6.03H9.97v7.313Zm3.376-3.375h-1.688V5.188a.843.843 0 0 0-.844-.844h-4.78V2.656h7.312V9.97Z"
            />
        </svg>
    );
}
 
export default SVGOpenLink;
