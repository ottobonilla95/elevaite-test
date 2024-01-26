import type { SVGProps } from "react"


function SVGArrowLong(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 8}
            width={props.size ? props.size * 3.625 : 29}
            viewBox="0 0 29 8"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                fill={mainColor}
                d="M28.104 4.354a.5.5 0 0 0 0-.708L24.922.464a.5.5 0 1 0-.707.708L27.043 4l-2.828 2.828a.5.5 0 1 0 .707.708l3.182-3.182ZM0 4.5h27.75v-1H0v1Z"
            />
        </svg>
    );
}
 
export default SVGArrowLong;
