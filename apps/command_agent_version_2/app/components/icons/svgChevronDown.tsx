import type { SVGProps, JSX } from "react";


export default function SVGChevronDown(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 10 6"
            width={props.size ? props.size * (10 / 6) : 10}
            height={props.size ?? 6}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M0.699951 0.700012L4.89995 4.90001L9.09995 0.700012"
            />
        </svg>
    );
}
