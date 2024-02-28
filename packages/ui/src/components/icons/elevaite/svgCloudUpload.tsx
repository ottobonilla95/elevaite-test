import type { SVGProps } from "react"


function SVGCloudUpload(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 18"
            width={props.size ? props.size * (20 / 18) : 20}
            height={props.size ? props.size : 18}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.667}
                d="M6.664 12.333 9.997 9m0 0 3.334 3.333M9.997 9v7.5m6.667-3.548a4.583 4.583 0 0 0-2.917-8.12.516.516 0 0 1-.444-.25 6.25 6.25 0 1 0-9.816 7.58"
            />
        </svg>
    );
}
 
export default SVGCloudUpload;
