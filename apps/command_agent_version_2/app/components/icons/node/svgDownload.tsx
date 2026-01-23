import type { SVGProps, JSX } from "react";


export default function SVGDownload(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                 d="M13.3 9.09995V9.93995C13.3 11.1161 13.3 11.7041 13.0711 12.1533C12.8697 12.5485 12.5485 12.8697 12.1533 13.0711C11.7041 13.3 11.1161 13.3 9.93995 13.3H4.05995C2.88384 13.3 2.29579 13.3 1.84657 13.0711C1.45143 12.8697 1.13017 12.5485 0.928837 12.1533C0.699951 11.7041 0.699951 11.1161 0.699951 9.93995V9.09995M10.5 5.59995L6.99995 9.09995M6.99995 9.09995L3.49995 5.59995M6.99995 9.09995V0.699951"
            />
        </svg>
    );
}
