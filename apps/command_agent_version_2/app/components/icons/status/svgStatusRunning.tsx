import type { SVGProps, JSX } from "react";


export default function SVGStatusRunning(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 11"
            width={props.size ? props.size * (12 / 11) : 12}
            height={props.size ?? 11}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.11615 0.559998L0.869854 5.31084C0.664393 5.4969 0.561662 5.58993 0.560092 5.6685C0.558727 5.7368 0.599059 5.80178 0.669464 5.84472C0.750452 5.8941 0.910922 5.8941 1.23186 5.8941H5.52711L4.93807 9.45017L10.1844 4.69933C10.3898 4.51327 10.4926 4.42024 10.4941 4.34167C10.4955 4.27337 10.4552 4.20839 10.3848 4.16546C10.3038 4.11607 10.1433 4.11607 9.82236 4.11607H5.52711L6.11615 0.559998Z"
            />
        </svg>
    );
}
