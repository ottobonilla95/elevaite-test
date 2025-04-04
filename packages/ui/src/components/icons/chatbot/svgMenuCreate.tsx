import type { SVGProps } from "react"


function SVGMenuCreate(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M9.167 3.333h-3.5c-1.4 0-2.1 0-2.635.273a2.5 2.5 0 0 0-1.093 1.092c-.272.535-.272 1.235-.272 2.635v7c0 1.4 0 2.1.272 2.635a2.5 2.5 0 0 0 1.093 1.093c.534.272 1.234.272 2.635.272h7c1.4 0 2.1 0 2.635-.272.47-.24.852-.622 1.092-1.093.273-.535.273-1.235.273-2.635v-3.5m-10 2.5h1.395c.408 0 .612 0 .803-.046.17-.04.333-.108.482-.2.168-.102.312-.246.6-.535l7.97-7.969a1.768 1.768 0 1 0-2.5-2.5l-7.97 7.97c-.288.287-.432.432-.535.6-.091.149-.159.311-.2.482-.045.191-.045.395-.045.803v1.395Z"
            />
        </svg>
    );
}
 
export default SVGMenuCreate;
