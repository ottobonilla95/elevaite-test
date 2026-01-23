import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGArrowLongRight(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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

function SVGArrowLongDown(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size * (33/15) : 33}
            width={props.size ? props.size : 15}
            viewBox="0 0 15 33"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                fill={mainColor}
                d="M6.793 32.707a1 1 0 0 0 1.414 0l6.364-6.364a1 1 0 0 0-1.414-1.414L7.5 30.586l-5.657-5.657A1 1 0 0 0 .43 26.343l6.364 6.364ZM6.5 0v32h2V0h-2Z"
            />
        </svg>
    );
}



function SVGArrowLong({type, ...props}: SVGProps<SVGSVGElement> & {type?: "down" | "right"}): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;


    switch(type) {
        case "down": return <SVGArrowLongDown  color={mainColor} {...props} />;
        case "right": return <SVGArrowLongRight color={mainColor} {...props} />;
        default: return <SVGArrowLongRight color={mainColor} {...props} />;
    }
}


 
export default SVGArrowLong;
