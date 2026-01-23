import type { SVGProps, JSX } from "react";


export default function SVGPrompt(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M6.3002 0.699951V11.9M10.5002 2.09995L2.1002 10.5M11.9002 6.29995H0.700195M10.5002 10.5L2.1002 2.09995"
            />
        </svg>
    );
}
