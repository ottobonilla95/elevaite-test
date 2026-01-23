import type { SVGProps, JSX } from "react";


export default function SVGScheduler(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                fill={mainColor}
                fillRule="evenodd"
                clipRule="evenodd"
                d="M0 7.7C0 3.44741 3.44741 0 7.7 0C11.9526 0 15.4 3.44741 15.4 7.7C15.4 11.9526 11.9526 15.4 7.7 15.4C3.44741 15.4 0 11.9526 0 7.7ZM8.4 3.5C8.4 3.1134 8.0866 2.8 7.7 2.8C7.3134 2.8 7 3.1134 7 3.5V7.7C7 7.96514 7.1498 8.20752 7.38695 8.3261L10.1869 9.7261C10.5327 9.89899 10.9532 9.75883 11.1261 9.41305C11.299 9.06726 11.1588 8.64679 10.813 8.4739L8.4 7.26738V3.5Z"
            />
        </svg>
    );
}
