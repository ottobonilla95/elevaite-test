import type { SVGProps, JSX } from "react";


export default function SVGMicrophone(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 16"
            width={props.size ? props.size * (12 / 16) : 12}
            height={props.size ?? 16}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10.5 6.29995V7.69995C10.5 10.4061 8.30615 12.6 5.59995 12.6M0.699951 6.29995V7.69995C0.699951 10.4061 2.89376 12.6 5.59995 12.6M5.59995 12.6V14.7M2.79995 14.7H8.39995M5.59995 9.79995C4.44015 9.79995 3.49995 8.85975 3.49995 7.69995V2.79995C3.49995 1.64015 4.44015 0.699951 5.59995 0.699951C6.75975 0.699951 7.69995 1.64015 7.69995 2.79995V7.69995C7.69995 8.85975 6.75975 9.79995 5.59995 9.79995Z"
            />
        </svg>
    );
}
