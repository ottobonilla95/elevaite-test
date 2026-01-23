import type { SVGProps, JSX } from "react";


export default function SVGDelete(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M4.9002 0.699951H9.1002M0.700195 2.79995H13.3002M11.9002 2.79995L11.4093 10.1635C11.3356 11.2682 11.2988 11.8206 11.0602 12.2395C10.8501 12.6082 10.5333 12.9047 10.1514 13.0897C9.71757 13.3 9.16396 13.3 8.05674 13.3H5.94365C4.83643 13.3 4.28282 13.3 3.84903 13.0897C3.46713 12.9047 3.15026 12.6082 2.94018 12.2395C2.70157 11.8206 2.66475 11.2682 2.5911 10.1635L2.1002 2.79995M5.6002 5.94995V9.44995M8.4002 5.94995V9.44995"
            />
        </svg>
    );
}
