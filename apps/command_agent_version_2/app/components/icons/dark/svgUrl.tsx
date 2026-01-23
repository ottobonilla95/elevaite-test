import type { SVGProps, JSX } from "react";


export default function SVGUrl(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 15 15"
            width={props.size ?? 15}
            height={props.size ?? 15}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M7.66477 11.6246L6.67482 12.6146C5.30799 13.9814 3.09191 13.9814 1.72508 12.6146C0.358242 11.2477 0.358243 9.03167 1.72508 7.66484L2.71503 6.67489M11.6246 7.66484L12.6145 6.67489C13.9814 5.30805 13.9814 3.09197 12.6145 1.72514C11.2477 0.358303 9.03161 0.358304 7.66477 1.72514L6.67482 2.71509M4.7198 9.61985L9.6198 4.71985"
            />
        </svg>
    );
}
