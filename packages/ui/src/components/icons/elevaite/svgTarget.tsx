import type { SVGProps } from "react"


function SVGTarget(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 16}
            width={props.size ? props.size : 16}
            viewBox="0 0 16 16"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <rect
                width={14}
                height={14}
                x={1}
                y={1}
                stroke={mainColor}
                strokeWidth={2}
                rx={7}
            />
            <circle
                cx={8}
                cy={8}
                r={2}
                fill={mainColor}
            />
        </svg>
    );
}
 
export default SVGTarget;
