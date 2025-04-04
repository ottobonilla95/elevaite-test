import type { SVGProps } from "react"


function SVGSettings(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 18 20"
            width={props.size ? props.size : 18}
            height={props.size ? props.size * (20/18) : 20}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="m6.83 16.143.486 1.095a1.844 1.844 0 0 0 3.37 0l.488-1.095a2.022 2.022 0 0 1 2.058-1.187l1.192.127a1.844 1.844 0 0 0 1.685-2.918l-.706-.97A2.024 2.024 0 0 1 15.02 10c0-.428.135-.845.387-1.19l.706-.97a1.842 1.842 0 0 0-.655-2.728 1.844 1.844 0 0 0-1.03-.19l-1.192.126a2.028 2.028 0 0 1-1.225-.26 2.022 2.022 0 0 1-.834-.93l-.49-1.096a1.844 1.844 0 0 0-3.37 0l-.488 1.095a2.021 2.021 0 0 1-2.058 1.191l-1.195-.127A1.843 1.843 0 0 0 1.89 7.84l.706.97a2.024 2.024 0 0 1 0 2.38l-.706.97a1.843 1.843 0 0 0 1.686 2.919l1.191-.127a2.028 2.028 0 0 1 2.062 1.19Z"
            />
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"
            />
        </svg>
    );
}
 
export default SVGSettings;
