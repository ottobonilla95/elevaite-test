import type { SVGProps } from "react"


function SVGDeployed(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 16 16"
            width={props.size ? props.size : 16}
            height={props.size ? props.size : 16}
            {...props}
        >
            <g fill={mainColor} clipPath="url(#a)">
                <path d="m8 7.233 3.95-2.284L8 2.666 4.05 4.95 8 7.233Zm-6 4.183V4.583l6-3.45 6 3.45v3.416h-1.333V6.066l-4.684 2.7-4.65-2.7v4.567L7.35 12.95v1.533L2 11.416Z" />
                <path d="m12.003 10.667-2 2 .466.466 1.2-1.2v2.734h.667v-2.734l1.2 1.2.467-.466-2-2Zm0-1.334a3.21 3.21 0 0 1 2.358.976c.65.65.974 1.436.975 2.358 0 .922-.325 1.708-.975 2.358-.65.65-1.437.975-2.358.975a3.213 3.213 0 0 1-2.36-.975 3.21 3.21 0 0 1-.974-2.358c0-.923.325-1.709.976-2.359a3.21 3.21 0 0 1 2.358-.975Z" />
            </g>
            <defs>
                <clipPath id="a">
                    <path fill="#fff" d="M0 0h16v16H0z" />
                </clipPath>
            </defs>
        </svg>
    );
}
 
export default SVGDeployed;
