import type { SVGProps, JSX } from "react";


export default function SVGRedo(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 13 13"
            width={props.size ?? 13}
            height={props.size ?? 13}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.9 3.5H4.9C2.5804 3.5 0.699997 5.3804 0.699997 7.7C0.699997 10.0196 2.5804 11.9 4.9 11.9H11.9M11.9 3.5L9.1 0.699997M11.9 3.5L9.1 6.3"
            />
        </svg>
    );

}