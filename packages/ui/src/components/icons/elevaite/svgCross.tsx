import type { SVGProps } from "react"


function SVGCross(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 12}
            viewBox="0 0 12 12"
            width={props.size ? props.size : 12}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M6 1.333v9.333M1.335 6h9.333"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
            />
        </svg>
    );
}
 
export default SVGCross;
