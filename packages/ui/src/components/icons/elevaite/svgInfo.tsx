import type { SVGProps } from "react"


function SVGInfo(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                clipRule="evenodd"
                d="M6 .5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11Zm0 3a.5.5 0 0 0 0 1h.005a.5.5 0 0 0 0-1H6ZM6.5 6a.5.5 0 0 0-1 0v2a.5.5 0 0 0 1 0V6Z"
                fill={mainColor}
                fillRule="evenodd"
            />
        </svg>
    );
}
 
export default SVGInfo;
