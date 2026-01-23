import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGInstructions(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 21 19"
            width={props.size ? props.size * (21/19) : 21}
            height={props.size ? props.size : 19}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="m19.5 16-1 1.094c-.53.58-1.25.906-2 .906a2.71 2.71 0 0 1-2-.906 2.716 2.716 0 0 0-2-.904c-.75 0-1.469.325-2 .904M1.5 18h1.675c.489 0 .733 0 .963-.055.205-.05.4-.13.579-.24.201-.123.374-.296.72-.642L18 4.5a2.121 2.121 0 1 0-3-3L2.437 14.063c-.346.346-.519.519-.642.72a2 2 0 0 0-.24.579c-.055.23-.055.474-.055.964V18Z"
            />
        </svg>
    );
}
 
export default SVGInstructions;
