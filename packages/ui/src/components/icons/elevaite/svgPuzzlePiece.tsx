import type { SVGProps } from "react"


function SVGPuzzlePiece(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 29 29"
            width={props.size ? props.size : 29}
            height={props.size ? props.size : 29}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.4}
                d="M9 5.4a3 3 0 0 1 6 0v1.8h1.2c1.677 0 2.516 0 3.178.274a3.6 3.6 0 0 1 1.948 1.948c.274.662.274 1.5.274 3.178h1.8a3 3 0 1 1 0 6h-1.8v2.04c0 2.016 0 3.024-.392 3.794a3.6 3.6 0 0 1-1.574 1.573c-.77.393-1.778.393-3.794.393H15v-2.1a2.7 2.7 0 1 0-5.4 0v2.1H8.16c-2.016 0-3.024 0-3.794-.392a3.6 3.6 0 0 1-1.574-1.574c-.392-.77-.392-1.778-.392-3.794V18.6h1.8a3 3 0 1 0 0-6H2.4c0-1.678 0-2.516.274-3.178a3.6 3.6 0 0 1 1.948-1.948C5.284 7.2 6.122 7.2 7.8 7.2H9V5.4Z"
            />
        </svg>
    );
}
 
export default SVGPuzzlePiece;
