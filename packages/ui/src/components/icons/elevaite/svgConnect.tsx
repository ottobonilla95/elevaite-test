import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGConnect(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 20}
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="M12.5 7.5v1.25H8.75a2.5 2.5 0 0 0-2.5 2.5v2.5a2.5 2.5 0 0 0 2.5 2.5H15a2.5 2.5 0 0 0 2.5-2.5v-2.5a2.5 2.5 0 0 0-1.25-2.165V7.712a3.752 3.752 0 0 1 2.5 3.537v2.5a3.75 3.75 0 0 1-3.75 3.75H8.75A3.75 3.75 0 0 1 5 13.749V11.25A3.75 3.75 0 0 1 8.75 7.5h3.75Z"
                fill={mainColor}
            />
            <path
                d="M7.5 12.5v-1.25h3.75a2.5 2.5 0 0 0 2.5-2.5v-2.5a2.5 2.5 0 0 0-2.5-2.5H5a2.5 2.5 0 0 0-2.5 2.5v2.5a2.5 2.5 0 0 0 1.25 2.165v1.373a3.752 3.752 0 0 1-2.5-3.538v-2.5A3.75 3.75 0 0 1 5 2.5h6.25A3.75 3.75 0 0 1 15 6.25v2.5a3.75 3.75 0 0 1-3.75 3.75H7.5Z"
                fill={mainColor}
            />
        </svg>
    );
}
 
export default SVGConnect;
