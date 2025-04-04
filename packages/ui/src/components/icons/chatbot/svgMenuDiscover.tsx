import type { SVGProps } from "react"


function SVGMenuDiscover(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M4.583 1.667a.833.833 0 1 0-1.666 0v1.25h-1.25a.833.833 0 0 0 0 1.666h1.25v1.25a.833.833 0 1 0 1.666 0v-1.25h1.25a.833.833 0 1 0 0-1.666h-1.25v-1.25ZM4.583 14.167a.833.833 0 1 0-1.666 0v1.25h-1.25a.833.833 0 1 0 0 1.666h1.25v1.25a.833.833 0 0 0 1.666 0v-1.25h1.25a.833.833 0 0 0 0-1.666h-1.25v-1.25ZM11.611 2.2a.833.833 0 0 0-1.555 0L8.61 5.959c-.25.651-.329.839-.436.99-.108.152-.24.284-.393.392-.151.108-.339.187-.99.437L3.035 9.222a.833.833 0 0 0 0 1.556l3.758 1.445c.65.25.838.329.99.436.151.108.284.241.392.393.107.151.186.339.436.99l1.446 3.757a.833.833 0 0 0 1.555 0l1.445-3.757c.25-.651.33-.839.437-.99.108-.152.24-.285.392-.393.152-.107.34-.186.99-.436l3.758-1.445a.833.833 0 0 0 0-1.556l-3.758-1.445c-.65-.25-.838-.329-.99-.437a1.666 1.666 0 0 1-.392-.392c-.108-.151-.186-.339-.437-.99l-1.445-3.757Z"
            />
        </svg>
    );
}
 
export default SVGMenuDiscover;
