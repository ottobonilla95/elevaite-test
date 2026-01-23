import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGFilter(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            width={props.size ? props.size : 13}
            height={props.size ? props.size : 14}
            viewBox="0 0 13 14"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                fill={mainColor}
                d="M7.778 7v6.127a.746.746 0 0 1-.226.646.774.774 0 0 1-1.096 0L4.892 12.21a.77.77 0 0 1-.225-.646V6.999h-.023L.164 1.26A.778.778 0 0 1 .296.172.81.81 0 0 1 .78 0h10.887a.81.81 0 0 1 .482.171.778.778 0 0 1 .132 1.089L7.8 7h-.022Z"
            />
        </svg>
    );
}
 
export default SVGFilter;
