import type { SVGProps } from "react"


function ChevronDown(props: SVGProps<SVGSVGElement>): JSX.Element {
    return (
        <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="m4 6.5 4 4 4-4" stroke={props.color ? props.color : "currentColor"} strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
        </svg>
    );
}

function ChevronRight(props: SVGProps<SVGSVGElement>): JSX.Element {
    return (
        <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="m6 12 4-4-4-4" stroke={props.color ? props.color : "currentColor"} strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
        </svg>
    );
}

function SVGChevron(props: SVGProps<SVGSVGElement> & {type?: "down" | "right"}): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;


    switch(props.type) {
        case "down": return <ChevronDown color={mainColor} />;
        case "right": return <ChevronRight color={mainColor} />;
        default: return <ChevronDown color={mainColor} />;
    }
}
 
export default SVGChevron;
