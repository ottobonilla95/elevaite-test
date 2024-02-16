import type { SVGProps } from "react"


function SVGSessions(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                fill={mainColor}
                d="m16.875 15.991-1.25-1.25v-1.616h-1.25v2.134l1.616 1.616.884-.884Z"
            />
            <path
                fill={mainColor}
                d="M15 19.375A4.38 4.38 0 0 1 10.625 15 4.38 4.38 0 0 1 15 10.625 4.38 4.38 0 0 1 19.375 15 4.38 4.38 0 0 1 15 19.375Zm0-7.5A3.129 3.129 0 0 0 11.875 15 3.129 3.129 0 0 0 15 18.125 3.129 3.129 0 0 0 18.125 15 3.129 3.129 0 0 0 15 11.875Zm2.5-2.5h1.25v-6.25c0-.69-.56-1.25-1.25-1.25h-1.875v1.25H17.5v6.25ZM5.625 9.375a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5ZM10 9.375a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5ZM14.375 9.375a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5Z"
            />
            <path
                fill={mainColor}
                d="M4.375 14.375H2.5c-.69 0-1.25-.56-1.25-1.25v-10c0-.69.56-1.25 1.25-1.25h1.875v1.25H2.5v10h1.875v1.25Z"
            />
        </svg>
    );
}
 
export default SVGSessions;
