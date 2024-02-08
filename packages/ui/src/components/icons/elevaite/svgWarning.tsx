import type { SVGProps } from "react"


function SVGWarning(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            width={props.size ? props.size : 18}
            height={props.size ? props.size : 18}
            viewBox="0 0 18 18"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                fill={mainColor}
                d="M8.061 8a.937.937 0 0 1 1.874 0v2.81a.937.937 0 0 1-1.874 0V8Zm0 5.62a.937.937 0 1 1 1.873 0 .937.937 0 0 1-1.874 0Z"
            />
                <path
                fill={mainColor}
                d="M10.656 1.63A1.872 1.872 0 0 0 9 .635a1.87 1.87 0 0 0-1.656.996L.47 14.616a1.86 1.86 0 0 0 .05 1.844 1.859 1.859 0 0 0 1.605.907h13.75a1.86 1.86 0 0 0 1.605-.907 1.863 1.863 0 0 0 .05-1.844L10.657 1.63Zm-8.53 13.863L9 2.507l6.88 12.986H2.124Z"
            />
        </svg>
    );
}
 
export default SVGWarning;
