import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGAccess(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
            <path
                fill={mainColor}
                d="M17.556 10.889c.333 0 .777 0 1.11.111V5.667L10.334 2 2 5.667v5.444c0 5 3.556 9.778 8.333 10.889.667-.111 1.223-.333 1.778-.556a6.735 6.735 0 0 1-1.222-3.888c0-3.667 3-6.667 6.667-6.667Zm0 2.222c-2.445 0-4.445 2-4.445 4.445 0 2.444 2 4.444 4.445 4.444C20 22 22 20 22 17.556c0-2.445-2-4.445-4.444-4.445Zm0 1.556c.666 0 1.222.555 1.222 1.222 0 .667-.556 1.222-1.222 1.222a1.233 1.233 0 0 1-1.223-1.222c0-.667.556-1.222 1.223-1.222Zm0 6c-1 0-1.89-.556-2.445-1.334.111-.777 1.667-1.222 2.445-1.222.777 0 2.444.445 2.444 1.222-.556.778-1.444 1.334-2.444 1.334Z"
            />
        </svg>
    );
}
 
export default SVGAccess;
