import type { SVGProps } from "react"


function SVGCheckmark(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            fill="none"
            height={props.size ? props.size : 12}
            viewBox="0 0 16 12"
            width={props.size ? (props.size / 3) * 4 : 16}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                d="m14.667 1-9.166 9.167L1.334 6"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
            />
        </svg>
    );
}
 
export default SVGCheckmark;
