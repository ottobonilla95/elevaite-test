import type { SVGProps } from "react"


function SVGInstanceProgress(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 18}
            viewBox="0 0 18 18"
            width={props.size ? props.size : 18}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M9 .25A8.75 8.75 0 1 0 17.75 9 8.76 8.76 0 0 0 9 .25ZM9 16.5a7.5 7.5 0 0 1 0-15V9l5.3 5.3A7.474 7.474 0 0 1 9 16.5Z"
                fill={mainColor}
            />
        </svg>
    );
}
 
export default SVGInstanceProgress;
