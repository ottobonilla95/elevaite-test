import type { SVGProps, JSX } from "react";


export default function SVGInfo(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.59998 8.99998V6.59998M6.59998 4.19998H6.60598M12.6 6.59998C12.6 9.91368 9.91368 12.6 6.59998 12.6C3.28627 12.6 0.599976 9.91368 0.599976 6.59998C0.599976 3.28627 3.28627 0.599976 6.59998 0.599976C9.91368 0.599976 12.6 3.28627 12.6 6.59998Z"
            />
        </svg>
    );
}
