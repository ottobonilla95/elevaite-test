import type { SVGProps } from "react"


function SVGUpload(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 16 16"
            width={props.size ? props.size : 16}
            height={props.size ? props.size : 16}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.75}
                d="M2.668 11.334v1.333a1.333 1.333 0 0 0 1.333 1.334h8a1.333 1.333 0 0 0 1.334-1.334v-1.333M11.336 6 8.003 2.665m0 0L4.669 5.999m3.334-3.333v8"
            />
        </svg>
    );
}
 
export default SVGUpload;
