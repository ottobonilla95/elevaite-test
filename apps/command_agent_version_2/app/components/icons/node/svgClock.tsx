import type { SVGProps, JSX } from "react";


export default function SVGClock(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 13 13"
            width={props.size ?? 13}
            height={props.size ?? 13}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.16006 2.80006V6.16006L8.40006 7.28006M11.7601 6.16006C11.7601 9.25285 9.25285 11.7601 6.16006 11.7601C3.06726 11.7601 0.560059 9.25285 0.560059 6.16006C0.560059 3.06726 3.06726 0.560059 6.16006 0.560059C9.25285 0.560059 11.7601 3.06726 11.7601 6.16006Z"
            />
        </svg>
    );
}
