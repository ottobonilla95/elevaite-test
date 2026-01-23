import type { SVGProps, JSX } from "react";


export default function SVGAddVariable(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 13"
            width={props.size ? props.size * (16 / 13) : 16}
            height={props.size ?? 13}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12.2996 11.9C13.183 11.9 13.8998 11.1839 13.8998 10.2998V7.10005L14.6999 6.29995L13.8998 5.49985V2.30015C13.8998 1.41605 13.1837 0.699951 12.2996 0.699951M3.1003 0.699951C2.2162 0.699951 1.5001 1.41605 1.5001 2.30015V5.49985L0.699997 6.29995L1.5001 7.10005V10.2998C1.5001 11.1839 2.2162 11.9 3.1003 11.9M7.7 3.49995V9.09995M4.9 6.29995H10.5"
            />
        </svg>
    );
}
