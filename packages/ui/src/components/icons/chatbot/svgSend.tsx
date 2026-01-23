import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGSend(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 18 16"
            width={props.size ? props.size * (18/16) : 18}
            height={props.size ? props.size : 16}
            {...props}
        >
            <path
                fill={mainColor}
                d="M17.438 8.554a1.25 1.25 0 0 0 0-1.109c-.152-.307-.42-.468-.557-.546a7.012 7.012 0 0 0-.53-.255L2.365.35A7.209 7.209 0 0 0 1.812.12c-.15-.052-.452-.147-.787-.054a1.25 1.25 0 0 0-.829.748C.07 1.136.133 1.447.17 1.6c.04.169.106.37.174.573l1.353 4.079c.11.328.164.492.265.614.09.107.205.19.335.241.147.058.32.058.666.058h6.036a.833.833 0 1 1 0 1.667H2.98c-.346 0-.518 0-.665.057a.833.833 0 0 0-.334.24c-.101.122-.156.286-.266.613L.35 13.819c-.068.203-.136.405-.176.574-.037.155-.102.466.025.79.143.366.45.644.828.75.336.093.639-.002.789-.054.164-.057.358-.144.553-.232l13.982-6.292c.19-.086.38-.171.53-.255.138-.078.405-.239.557-.546Z"
            />
        </svg>
    );
}
 
export default SVGSend;
