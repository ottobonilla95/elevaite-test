import type { SVGProps } from "react"


function SVGDownloadExport(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    // let mainColor = "currentColor";
    let mainColor = "var(--ev-colors-text)";
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
                d="M1.668 10.333v1.333a1.333 1.333 0 0 0 1.333 1.333h8a1.333 1.333 0 0 0 1.334-1.333v-1.333m-8.667-4 3.333 3.333m0 0 3.334-3.333M7 9.666v-8"
            />
        </svg>
    );
}
 
export default SVGDownloadExport;
