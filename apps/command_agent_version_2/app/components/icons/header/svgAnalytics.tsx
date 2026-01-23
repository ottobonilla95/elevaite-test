import type { SVGProps, JSX } from "react";


export default function SVGAnalytics(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeOpacity={0.72}
                strokeWidth={1.5}
                d="M13.35 13.35H1.87c-.392 0-.588 0-.738-.076a.7.7 0 0 1-.306-.306c-.076-.15-.076-.346-.076-.738V.75m12.6 2.8L9.546 7.354c-.139.139-.208.208-.288.234a.35.35 0 0 1-.216 0c-.08-.026-.15-.095-.288-.234L7.446 6.046c-.139-.139-.208-.208-.288-.234a.35.35 0 0 0-.216 0c-.08.026-.15.095-.288.234L3.55 9.15m9.8-5.6h-2.8m2.8 0v2.8"
            />
        </svg>
    );
}
 
