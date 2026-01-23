import type { SVGProps, JSX } from "react";


export default function SVGSearch(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M13.3 13.3L10.255 10.255M11.9 6.30001C11.9 9.39281 9.39275 11.9 6.29995 11.9C3.20716 11.9 0.699951 9.39281 0.699951 6.30001C0.699951 3.20722 3.20716 0.700012 6.29995 0.700012C9.39275 0.700012 11.9 3.20722 11.9 6.30001Z"
            />
        </svg>
    );
}
