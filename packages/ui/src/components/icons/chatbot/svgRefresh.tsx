import type { SVGProps } from "react"


function SVGRefresh(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            width={props.size ? props.size : 16}
            height={props.size ? props.size : 16}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.75}
                d="M2.5 2v6h6M2.66 15.57a10 10 0 1 0 .57-8.38"
                // d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"

                // d="M2.668 11.334v1.333a1.333 1.333 0 0 0 1.333 1.334h8a1.333 1.333 0 0 0 1.334-1.334v-1.333M11.336 6 8.003 2.665m0 0L4.669 5.999m3.334-3.333v8"
            />
        </svg>
    );
}

export default SVGRefresh;