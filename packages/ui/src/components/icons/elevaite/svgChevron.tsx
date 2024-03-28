import type { SVGProps } from "react"


function ChevronDown(props: SVGProps<SVGSVGElement>): JSX.Element {
    return (
        <svg fill="none" viewBox="0 0 16 16" width={16} height={16} xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="m4 6.5 4 4 4-4" stroke={props.color ? props.color : "currentColor"} strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
        </svg>
    );
}

function ChevronRight(props: SVGProps<SVGSVGElement>): JSX.Element {
    return (
        <svg fill="none" viewBox="0 0 16 16" width={16} height={16} xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="m6 12 4-4-4-4" stroke={props.color ? props.color : "currentColor"} strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
        </svg>
    );
}

function ChevronSort(props: SVGProps<SVGSVGElement>): JSX.Element {
    return (
        <svg fill="none" viewBox="0 0 10 6" width={10} height={6} xmlns="http://www.w3.org/2000/svg" {...props}>
        <path
            stroke={props.color ? props.color : "currentColor"}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="m1 1 4 4 4-4"
        />
        </svg>
    );
}



function SVGChevron(props: SVGProps<SVGSVGElement> & {type?: "down" | "right" | "sort"}): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;


    switch(props.type) {
        case "down": return <ChevronDown color={mainColor} />;
        case "right": return <ChevronRight color={mainColor} />;
        case "sort": return <ChevronSort color={mainColor} />;
        default: return <ChevronDown color={mainColor} />;
    }
}
 
export default SVGChevron;
