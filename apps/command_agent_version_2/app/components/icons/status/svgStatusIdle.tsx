import type { SVGProps, JSX } from "react";


export default function SVGStatusIdle(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 14 14"
            width={props.size ?? 14}
            height={props.size ?? 14}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.59301 2.97318V6.59295L9.00619 7.79954M12.626 6.59295C12.626 9.92486 9.92492 12.6259 6.59301 12.6259C3.2611 12.6259 0.560059 9.92486 0.560059 6.59295C0.560059 3.26104 3.2611 0.559998 6.59301 0.559998C9.92492 0.559998 12.626 3.26104 12.626 6.59295Z"
            />
        </svg>
    );
}
