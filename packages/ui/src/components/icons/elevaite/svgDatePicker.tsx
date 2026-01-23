import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGDatePicker(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            width={props.size ? props.size : 24}
            height={props.size ? props.size : 24}
            {...props}
        >
            <g fill={mainColor} clipPath="url(#a)">
                <path d="M14.25 21h-12A2.247 2.247 0 0 1 0 18.75V3.57a2.247 2.247 0 0 1 2.25-2.25h16.5A2.247 2.247 0 0 1 21 3.57v10.875c0 .42-.33.75-.75.75s-.75-.33-.75-.75V3.57c0-.42-.33-.75-.75-.75H2.25c-.42 0-.75.33-.75.75v15.18c0 .42.33.75.75.75h12c.42 0 .75.33.75.75s-.33.75-.75.75Z" />
                <path d="M6 5.43c-.42 0-.75-.33-.75-.75V.75C5.25.33 5.58 0 6 0s.75.33.75.75v3.93c0 .42-.33.75-.75.75Zm9.18 0c-.42 0-.75-.33-.75-.75V.75c0-.42.33-.75.75-.75s.75.33.75.75v3.93c0 .42-.33.75-.75.75ZM20.25 9H.75C.33 9 0 8.67 0 8.25s.33-.75.75-.75h19.5c.42 0 .75.33.75.75s-.33.75-.75.75Zm-1.5 15a5.256 5.256 0 0 1-5.25-5.25 5.256 5.256 0 0 1 5.25-5.25A5.256 5.256 0 0 1 24 18.75 5.256 5.256 0 0 1 18.75 24Zm0-9a3.75 3.75 0 1 0 0 7.5 3.75 3.75 0 0 0 0-7.5Z" />
                <path d="M20.25 21a.704.704 0 0 1-.525-.225l-1.5-1.5A.75.75 0 0 1 18 18.75V16.5c0-.42.33-.75.75-.75s.75.33.75.75v1.935l1.275 1.275c.3.3.3.765 0 1.065a.753.753 0 0 1-.525.225Z" />
            </g>
            <defs>
                <clipPath id="a">
                    <path fill="#fff" d="M0 0h24v24H0z" />
                </clipPath>
            </defs>
        </svg>
    );
}
 
export default SVGDatePicker;
