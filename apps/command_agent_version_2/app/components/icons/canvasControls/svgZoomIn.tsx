import type { SVGProps, JSX } from "react";


export default function SVGZoomIn(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 14 14"
            width={props.size ?? 14}
            height={props.size ?? 14}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.3 13.3L10.255 10.255M6.30001 4.2V8.4M4.20001 6.3H8.40001M11.9 6.3C11.9 9.39279 9.39281 11.9 6.30001 11.9C3.20722 11.9 0.700012 9.39279 0.700012 6.3C0.700012 3.2072 3.20722 0.699997 6.30001 0.699997C9.39281 0.699997 11.9 3.2072 11.9 6.3Z"
            />
        </svg>
    );
}
