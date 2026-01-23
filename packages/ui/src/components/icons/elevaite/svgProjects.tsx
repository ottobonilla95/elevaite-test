import type { JSX } from "react";

import type { SVGProps } from "react"


function SVGProjects(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            height={props.size ? props.size : 24}
            width={props.size ? props.size : 24}
            fill="none"
            {...props}
        >
            <g clipPath="url(#a)">
                <path
                    fill={mainColor}
                    d="M2.625 0h18.75A2.626 2.626 0 0 1 24 2.625v18.75A2.625 2.625 0 0 1 21.375 24H2.625A2.625 2.625 0 0 1 0 21.375V2.625A2.626 2.626 0 0 1 2.625 0ZM2.25 2.625v18.75c0 .207.168.375.375.375h18.75a.375.375 0 0 0 .375-.375V2.625a.375.375 0 0 0-.375-.375H2.625a.375.375 0 0 0-.375.375ZM17.625 4.5a1.125 1.125 0 0 1 1.125 1.125v11.25a1.125 1.125 0 1 1-2.25 0V5.625A1.125 1.125 0 0 1 17.625 4.5ZM5.25 5.625a1.125 1.125 0 0 1 2.25 0v8.25a1.125 1.125 0 0 1-2.25 0v-8.25ZM12 4.5a1.125 1.125 0 0 1 1.125 1.125v5.25a1.125 1.125 0 1 1-2.25 0v-5.25A1.125 1.125 0 0 1 12 4.5Z"
                />
            </g>
            <defs>
            <clipPath id="a">
                <path fill="#fff" d="M0 0h24v24H0z" />
            </clipPath>
            </defs>
        </svg>
    );
}
 
export default SVGProjects;
