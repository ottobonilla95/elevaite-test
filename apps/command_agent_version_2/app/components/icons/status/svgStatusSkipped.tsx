import type { SVGProps, JSX } from "react";


export default function SVGStatusSkipped(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 9 7"
            width={props.size ? props.size * (9 / 7) : 9}
            height={props.size ?? 7}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M7.7996 0.560028L0.560059 6.02324M0.560059 0.560028L7.7996 6.02324"
            />
        </svg>
    );
}
