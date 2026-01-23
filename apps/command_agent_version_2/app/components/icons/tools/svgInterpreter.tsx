import type { SVGProps, JSX } from "react";


export default function SVGInterpreter(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width={props.size ?? 24}
            height={props.size ?? 24}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="m8 8-4 4 4 4m8 0 4-4-4-4m-2-3-4 14"
            />
        </svg>
    );
}
