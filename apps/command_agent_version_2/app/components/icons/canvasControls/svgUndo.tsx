import type { SVGProps, JSX } from "react";


export default function SVGUndo(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M0.699997 3.5H7.7C10.0196 3.5 11.9 5.3804 11.9 7.7C11.9 10.0196 10.0196 11.9 7.7 11.9H0.699997M0.699997 3.5L3.5 0.699997M0.699997 3.5L3.5 6.3"
            />
        </svg>
    )
}
