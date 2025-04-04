import type { SVGProps } from "react"


function SVGActionCopy(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            height={props.size ? props.size : 20}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4.167 12.5c-.777 0-1.165 0-1.472-.127a1.666 1.666 0 0 1-.902-.902c-.126-.306-.126-.694-.126-1.471V4.333c0-.933 0-1.4.181-1.756.16-.314.415-.569.729-.729.356-.181.823-.181 1.756-.181H10c.777 0 1.165 0 1.471.127.409.169.733.493.902.902.127.306.127.694.127 1.47m-2.333 14.167h5.5c.933 0 1.4 0 1.756-.181.314-.16.569-.415.729-.729.181-.356.181-.823.181-1.756v-5.5c0-.934 0-1.4-.181-1.757a1.667 1.667 0 0 0-.729-.728C17.067 7.5 16.6 7.5 15.667 7.5h-5.5c-.934 0-1.4 0-1.757.182-.314.16-.569.414-.728.728-.182.357-.182.823-.182 1.757v5.5c0 .933 0 1.4.182 1.756.16.314.414.569.728.729.356.181.823.181 1.757.181Z"
              />
        </svg>
    );
}
 
export default SVGActionCopy;
