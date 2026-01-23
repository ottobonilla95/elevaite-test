import type { SVGProps, JSX } from "react";


export default function SVGClose(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 10 10"
            width={props.size ?? 10}
            height={props.size ?? 10}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.09995 0.700012L0.699951 9.10001M0.699951 0.700012L9.09995 9.10001"
            />
        </svg>
    );
}
