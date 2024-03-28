import type { SVGProps } from "react"


function SVGCopy(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                fill={mainColor}
                d="M13.5 1.75h-8a.75.75 0 0 0-.75.75v2.25H2.5a.75.75 0 0 0-.75.75v8a.75.75 0 0 0 .75.75h8a.75.75 0 0 0 .75-.75v-2.25h2.25a.75.75 0 0 0 .75-.75v-8a.75.75 0 0 0-.75-.75Zm-3.75 11h-6.5v-6.5h6.5v6.5Zm3-3h-1.5V5.5a.75.75 0 0 0-.75-.75H6.25v-1.5h6.5v6.5Z"
            />
        </svg>
    );
}
 
export default SVGCopy;
