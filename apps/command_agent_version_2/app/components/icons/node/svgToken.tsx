import type { SVGProps, JSX } from "react";


export default function SVGToken(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeWidth={1.44}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.52534 8.5251C10.442 8.2685 11.9202 6.62686 11.9202 4.63997C11.9202 2.47501 10.1652 0.719971 8.00021 0.719971C6.01332 0.719971 4.37169 2.19819 4.11508 4.11484M8.56021 7.99997C8.56021 10.1649 6.80517 11.92 4.64021 11.92C2.47526 11.92 0.720215 10.1649 0.720215 7.99997C0.720215 5.83501 2.47526 4.07997 4.64021 4.07997C6.80517 4.07997 8.56021 5.83501 8.56021 7.99997Z"
            />
        </svg>
    );
}
