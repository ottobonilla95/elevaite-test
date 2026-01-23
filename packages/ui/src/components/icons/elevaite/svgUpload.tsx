import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGUpload(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 14 16"
            width={props.size ? props.size : 14}
            height={props.size ? props.size * (16 / 14) : 16}
            {...props}
        >
            <path
                fill={mainColor}
                stroke={mainColor}
                strokeWidth={0.4}
                d="M7.431 1.001a.687.687 0 0 0-.97 0L3.217 4.244a.687.687 0 0 0 .97.97l.001.001L6.26 3.144v6.991a.687.687 0 0 0 1.373 0V3.144l2.072 2.071a.687.687 0 0 0 .97 0l-.14-.141.14.141a.687.687 0 0 0 0-.97L7.432 1Zm-5.15 10.215a.74.74 0 1 0-1.481 0v1.622A2.359 2.359 0 0 0 3.158 15.2h7.573a2.361 2.361 0 0 0 2.361-2.362v-1.622a.74.74 0 1 0-1.481 0v1.622a.88.88 0 0 1-.88.88H3.158a.878.878 0 0 1-.877-.88v-1.622Z"
            />
        </svg>
    );
}
 
export default SVGUpload;
