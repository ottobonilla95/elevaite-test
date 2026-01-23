import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGMenuScorecard(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 18 18"
            width={props.size ? props.size : 18}
            height={props.size ? props.size : 18}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M6.5 9H2.833c-.466 0-.7 0-.878.09a.833.833 0 0 0-.364.365c-.091.178-.091.412-.091.878v4.834c0 .466 0 .7.09.878.08.157.208.284.365.364.178.091.412.091.878.091H6.5m0 0h5m-5 0V6.167c0-.467 0-.7.09-.879a.833.833 0 0 1 .365-.364c.178-.09.412-.09.878-.09h2.334c.466 0 .7 0 .878.09.157.08.284.208.364.364.091.179.091.412.091.879V16.5m0 0h3.667c.466 0 .7 0 .878-.09a.833.833 0 0 0 .364-.365c.091-.178.091-.412.091-.878V2.833c0-.466 0-.7-.09-.878a.833.833 0 0 0-.365-.364c-.178-.091-.412-.091-.878-.091h-2.334c-.466 0-.7 0-.878.09a.833.833 0 0 0-.364.365c-.091.178-.091.412-.091.878v2.834"
            />
        </svg>
    );
}
 
export default SVGMenuScorecard;
