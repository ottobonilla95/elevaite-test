import type { SVGProps } from "react"


function SVGDot(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg fill="none" height={props.size ? props.size : 5} viewBox="0 0 5 5" width={props.size ? props.size : 5} xmlns="http://www.w3.org/2000/svg">
            <circle cx="2.33325" cy="2" fill={mainColor} r="2" />
        </svg>
    );
}
 
export default SVGDot;
