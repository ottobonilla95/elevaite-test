import type { SVGProps } from "react"


function SVGEvaluate(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M29.335 9.334h-12V12h12V9.334Zm0 10.666h-12v2.667h12V20ZM7.388 14.667l-4.72-4.72 1.88-1.88 2.827 2.827 5.653-5.654 1.88 1.88-7.52 7.547Zm0 10.667-4.72-4.72 1.88-1.88 2.827 2.826 5.653-5.653 1.88 1.88-7.52 7.547Z"
            />
        </svg>
    );
}
 
export default SVGEvaluate;
