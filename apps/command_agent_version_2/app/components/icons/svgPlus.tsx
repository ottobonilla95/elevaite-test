import type { SVGProps, JSX } from "react";


export default function SVGPlus(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 12"
            width={props.size ?? 12}
            height={props.size ?? 12}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.43389}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5.73564 0.716919V10.7541M0.717041 5.73552H10.7542"
            />
        </svg>
    );
}
