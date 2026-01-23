import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGDatasets(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 22 22"
            width={props.size ? props.size : 22}
            height={props.size ? props.size : 22}
            {...props}
        >
            <path
                fill={mainColor}
                fillRule="evenodd"
                d="M.106 10.552a1 1 0 0 1 1.341-.447L11 14.882l9.553-4.777a1 1 0 0 1 .894 1.789l-9.642 4.821-.025.013c-.094.048-.287.146-.503.187a1.5 1.5 0 0 1-.553 0c-.217-.04-.41-.14-.503-.187l-.026-.013-9.642-4.821a1 1 0 0 1-.447-1.342Z"
                clipRule="evenodd"
            />
            <path
                fill={mainColor}
                fillRule="evenodd"
                d="M.106 15.552a1 1 0 0 1 1.341-.447L11 19.881l9.553-4.776a1 1 0 0 1 .894 1.789l-9.642 4.821-.025.013c-.094.048-.287.146-.503.187a1.5 1.5 0 0 1-.553 0c-.217-.04-.41-.14-.503-.187l-.026-.013-9.642-4.821a1 1 0 0 1-.447-1.342ZM10.724.084a1.5 1.5 0 0 1 .553 0c.216.04.41.14.503.187l.025.013 9.642 4.821a1 1 0 0 1 0 1.789l-9.642 4.821-.025.013c-.094.048-.287.146-.503.187a1.5 1.5 0 0 1-.553 0c-.217-.04-.41-.14-.503-.187l-.026-.013L.553 6.894a1 1 0 0 1 0-1.789L10.195.284l.026-.013c.093-.048.286-.146.503-.187Z"
                clipRule="evenodd"
            />
        </svg>
    );
}
 
export default SVGDatasets;
