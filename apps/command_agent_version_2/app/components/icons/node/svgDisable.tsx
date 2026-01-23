import type { SVGProps, JSX } from "react";


export default function SVGDisable(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M4.9002 7.69995H10.5002M14.7002 7.69995C14.7002 11.5659 11.5662 14.7 7.7002 14.7C3.8342 14.7 0.700195 11.5659 0.700195 7.69995C0.700195 3.83396 3.8342 0.699951 7.7002 0.699951C11.5662 0.699951 14.7002 3.83396 14.7002 7.69995Z"
            />
        </svg>
    );
}
