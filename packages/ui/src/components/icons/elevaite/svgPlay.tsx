import type { SVGProps } from "react"


function SVGPlay(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            width={props.size ? props.size : 24}
            height={props.size ? props.size : 24}
            {...props}
        >
            <path
                stroke="#fff"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeOpacity={0.5}
                strokeWidth={2}
                d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10Z"
            />
            <path
                fill={mainColor}
                d="M9.5 8.965c0-.477 0-.716.1-.85a.5.5 0 0 1 .364-.198c.166-.012.367.117.769.375l4.72 3.035c.349.224.523.336.583.478a.5.5 0 0 1 0 .39c-.06.142-.234.254-.583.478l-4.72 3.034c-.402.258-.603.387-.769.376a.5.5 0 0 1-.364-.2c-.1-.133-.1-.371-.1-.849V8.965Z"
            />
        </svg>
    );
}
 
export default SVGPlay;
