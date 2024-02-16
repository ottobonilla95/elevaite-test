import type { SVGProps } from "react"


function SVGMessage(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 18 18"
            width={props.size ? props.size : 18}
            height={props.size ? props.size : 18}
            {...props}
        >
            <path
                fill={mainColor}
                d="M2.335 2.333h13.333v10H3.31l-.975.975V2.333Zm0-1.667c-.917 0-1.659.75-1.659 1.667l-.008 15 3.333-3.334h11.667c.917 0 1.667-.75 1.667-1.666v-10c0-.917-.75-1.667-1.667-1.667H2.335ZM4 9.833c0-.46.373-.834.834-.834h5a.833.833 0 1 1 0 1.667h-5A.833.833 0 0 1 4 9.833Zm0-2.5c0-.46.373-.834.834-.834h8.333a.833.833 0 0 1 0 1.667H4.835A.833.833 0 0 1 4 7.333Zm0-2.5c0-.46.373-.834.834-.834h8.333a.833.833 0 0 1 0 1.667H4.835A.833.833 0 0 1 4 4.833Z"
            />
        </svg>
    );
}
 
export default SVGMessage;
