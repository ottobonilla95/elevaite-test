import type { JSX } from "react";
import type { SVGProps } from "react"


function Preprocess(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 44}
            viewBox="0 0 44 44"
            width={props.size ? props.size : 44}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <rect width={43.579} height={43.579} x={0.421} fill="#2EB67D" rx={21.79} />
            <path
                stroke="#fff"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12.21 29.79h5m-5-4h10m-1 4h2.5m5 0h3.5m-4.5-4h4.5m-6-4h6m-14 0h3m-9 0h1m-1-4h2m-2-4h3.5l4 4h12.5m-11-4h11"
            />
        </svg>
    );
}
 
export default Preprocess;