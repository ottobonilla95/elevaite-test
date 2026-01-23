import type { SVGProps, JSX } from "react";


export default function SVGMinimap(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            width={props.size ?? 16}
            height={props.size ?? 16}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5.60001 11.9L0.700012 14.7V3.5L5.60001 0.700005M5.60001 11.9L10.5 14.7M5.60001 11.9V0.700005M10.5 14.7L14.7 11.9V0.700005L10.5 3.5M10.5 14.7V3.5M10.5 3.5L5.60001 0.700005"
            />
        </svg>
    );
}
