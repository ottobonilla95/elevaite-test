import type { SVGProps, JSX } from "react";


export default function SVGArrowBack(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 13 10"
            width={props.size ? props.size * (13 / 10) : 13}
            height={props.size ?? 10}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.4}
                d="M11.635 4.8H.7m0 0 4.1 4.101m-4.1-4.1L4.8.7"
            />
        </svg>
    );
}