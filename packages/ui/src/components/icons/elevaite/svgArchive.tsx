import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGArchive(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 16 14"
            width={props.size ? props.size * (16/14) : 16}
            height={props.size ? props.size : 14}
            {...props}
        >
            <path
                fill={mainColor}
                fillRule="evenodd"
                d="M.668 2.334a2 2 0 0 1 2-2h10.667a2 2 0 1 1 0 4H2.668a2 2 0 0 1-2-2ZM2.668 5.667a.667.667 0 0 0-.667.667v3.494c0 .537 0 .98.03 1.34.03.375.096.72.26 1.043.257.502.665.91 1.166 1.166.324.164.668.23 1.043.26.36.03.804.03 1.34.03h4.322c.537 0 .98 0 1.34-.03.375-.03.72-.096 1.043-.26.502-.256.91-.664 1.166-1.166.165-.323.23-.668.26-1.043.03-.36.03-.803.03-1.34V6.334a.667.667 0 0 0-.666-.667H2.668Zm4 2a.667.667 0 1 0 0 1.334h2.667a.667.667 0 0 0 0-1.334H6.668Z"
                clipRule="evenodd"
            />
        </svg>
    );
}
 
export default SVGArchive;
