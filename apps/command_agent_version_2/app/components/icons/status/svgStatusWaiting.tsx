import type { SVGProps, JSX } from "react";


export default function SVGStatusWaiting(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 11 3"
            width={props.size ? props.size * (11 / 3) : 11}
            height={props.size ?? 3}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4.48002 1.12C4.48002 1.42928 4.73074 1.68 5.04002 1.68C5.3493 1.68 5.60002 1.42928 5.60002 1.12C5.60002 0.810718 5.3493 0.559998 5.04002 0.559998C4.73074 0.559998 4.48002 0.810718 4.48002 1.12Z"
            />
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.40002 1.12C8.40002 1.42928 8.65074 1.68 8.96002 1.68C9.2693 1.68 9.52002 1.42928 9.52002 1.12C9.52002 0.810718 9.2693 0.559998 8.96002 0.559998C8.65074 0.559998 8.40002 0.810718 8.40002 1.12Z"
            />
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M0.560019 1.12C0.560019 1.42928 0.81074 1.68 1.12002 1.68C1.4293 1.68 1.68002 1.42928 1.68002 1.12C1.68002 0.810718 1.4293 0.559998 1.12002 0.559998C0.81074 0.559998 0.560019 0.810718 0.560019 1.12Z"
            />
        </svg>
    );
}
