import type { SVGProps, JSX } from "react";


export default function SVGSimpleView(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 12"
            width={props.size ? props.size * (16 / 12) : 16}
            height={props.size ?? 12}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4.20001 5.90868L0.700012 7.65868L7.44957 11.0335C7.5414 11.0794 7.58731 11.1023 7.63547 11.1114C7.67813 11.1194 7.7219 11.1194 7.76455 11.1114C7.81271 11.1023 7.85862 11.0794 7.95045 11.0335L14.7 7.65868L11.2 5.90868M0.700012 4.15868L7.44957 0.783905C7.5414 0.737991 7.58731 0.715034 7.63547 0.705999C7.67813 0.697996 7.7219 0.697996 7.76455 0.705999C7.81271 0.715034 7.85862 0.737991 7.95045 0.783905L14.7 4.15868L7.95045 7.53346C7.85862 7.57938 7.81271 7.60234 7.76455 7.61137C7.7219 7.61937 7.67813 7.61937 7.63547 7.61137C7.58731 7.60234 7.5414 7.57938 7.44957 7.53346L0.700012 4.15868Z"
            />
        </svg>
    );
}