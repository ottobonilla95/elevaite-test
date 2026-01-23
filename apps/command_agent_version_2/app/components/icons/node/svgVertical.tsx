import type { SVGProps, JSX } from "react";


export default function SVGVertical(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 14 13"
            width={props.size ? props.size * (14 / 13) : 14}
            height={props.size ?? 13}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.5002 0.699951V11.9M3.5002 11.9L0.700195 9.09995M3.5002 11.9L6.3002 9.09995M10.5002 11.9V0.699951M10.5002 0.699951L7.7002 3.49995M10.5002 0.699951L13.3002 3.49995"
            />
        </svg>
    );
}
