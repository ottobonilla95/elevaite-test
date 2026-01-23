import type { SVGProps, JSX } from "react";


export default function SVGZoomOut(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 17 17"
            width={props.size ?? 17}
            height={props.size ?? 17}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14.7 14.7L11.655 11.655M5.60004 7.69999H9.80004M13.3 7.69999C13.3 10.7928 10.7928 13.3 7.70004 13.3C4.60724 13.3 2.10004 10.7928 2.10004 7.69999C2.10004 4.6072 4.60724 2.09999 7.70004 2.09999C10.7928 2.09999 13.3 4.6072 13.3 7.69999Z"
            />
        </svg>
    );
}