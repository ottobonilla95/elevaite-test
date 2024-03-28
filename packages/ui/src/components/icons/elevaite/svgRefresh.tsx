import type { SVGProps } from "react"
import "./svgRefresh.scss";


function SVGRefresh({className, ...props}: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            className={["svg-refresh", className].filter(Boolean).join(" ")}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            height={props.size ? props.size : 20}
            {...props}
        >
            <path
                fill={mainColor}
                d="M10.067 1.875c-3.995 0-7.278 3.053-7.598 6.944h-.8a.625.625 0 0 0-.44 1.07l1.4 1.388a.625.625 0 0 0 .88 0l1.4-1.389a.625.625 0 0 0-.44-1.069h-.745c.317-3.192 3.032-5.694 6.343-5.694a6.382 6.382 0 0 1 5.448 3.036.624.624 0 1 0 1.064-.655 7.631 7.631 0 0 0-6.512-3.631Z"
            />
            <path
                fill={mainColor}
                d="M17.37 8.723a.625.625 0 0 0-.879 0l-1.406 1.389a.625.625 0 0 0 .44 1.07h.748c-.317 3.191-3.042 5.694-6.37 5.694a6.415 6.415 0 0 1-5.47-3.037.624.624 0 1 0-1.064.657 7.664 7.664 0 0 0 6.534 3.63c4.007 0 7.305-3.05 7.626-6.944h.806a.625.625 0 0 0 .44-1.07l-1.406-1.389Z"
            />
        </svg>
    );
}
 
export default SVGRefresh;
