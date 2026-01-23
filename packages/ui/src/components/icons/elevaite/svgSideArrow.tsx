import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGSideArrow(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 32 32"
            width={props.size ? props.size : 32}
            height={props.size ? props.size : 32}
            {...props}
        >
            <path
                fill={mainColor}
                d="M31.218 15.838a1.18 1.18 0 0 0-.031-.159l.002.008a1.218 1.218 0 0 0-.305-.571v.001l-5-5a1.25 1.25 0 1 0-1.77 1.768l2.867 2.866H7.999a1.25 1.25 0 0 0 0 2.5H26.98l-2.866 2.865a1.25 1.25 0 0 0 1.769 1.769l5-5.001c.012-.012.016-.029.027-.041.099-.103.18-.223.239-.356l.003-.008v-.003a1.205 1.205 0 0 0 .063-.645l.001.007zM2 .75C1.31.75.75 1.31.75 2v28a1.25 1.25 0 0 0 2.5 0V2C3.25 1.31 2.69.75 2 .75z"
            />
        </svg>
    );
}
 
export default SVGSideArrow;
