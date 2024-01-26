import type { SVGProps } from "react"


function SVGMenuDots(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 14}
            viewBox="0 0 4 14"
            width={props.size ? (props.size / 7) * 2 : 4}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M2 7.667a.667.667 0 1 0 0-1.333.667.667 0 0 0 0 1.333ZM2 3a.667.667 0 1 0 0-1.333A.667.667 0 0 0 2 3ZM2 12.334A.667.667 0 1 0 2 11a.667.667 0 0 0 0 1.334Z"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
            />
        </svg>
    );
}
 
export default SVGMenuDots;
