import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGClear(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 17 16"
            width={props.size ? props.size * (17/16) : 17}
            height={props.size ? props.size : 16}
            {...props}
        >
            <path
                fill={mainColor}
                d="M3.422 15.705h10.161c1.75 0 2.62-.87 2.62-2.594V2.89c0-1.725-.87-2.595-2.62-2.595H3.422C1.68.295.793 1.157.793 2.89V13.11c0 1.732.887 2.594 2.629 2.594Zm2.109-4a.754.754 0 0 1-.753-.745c0-.193.083-.377.234-.528l2.427-2.444-2.427-2.436a.746.746 0 0 1-.234-.527c0-.419.342-.762.753-.762.2 0 .377.075.527.226l2.445 2.444 2.444-2.444a.705.705 0 0 1 .519-.226.764.764 0 0 1 .761.762.746.746 0 0 1-.234.527L9.557 7.988l2.436 2.444c.15.151.234.335.234.528 0 .41-.343.745-.761.745a.722.722 0 0 1-.511-.21l-2.452-2.46-2.453 2.46a.727.727 0 0 1-.52.21Z"
            />
        </svg>
    );
}
 
export default SVGClear;
