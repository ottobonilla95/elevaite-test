import type { SVGProps, JSX } from "react";


export default function SVGExpand(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M8.40001 5.6L13.3 0.700001M13.3 0.700001H9.10001M13.3 0.700001V4.9M5.60001 8.4L0.700012 13.3M0.700012 13.3H4.90001M0.700012 13.3L0.700012 9.1"
            />
        </svg>
    );
}
