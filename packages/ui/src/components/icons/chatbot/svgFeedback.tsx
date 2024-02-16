import type { SVGProps } from "react"


function SVGFeedback(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 14 14"
            width={props.size ? props.size : 14}
            height={props.size ? props.size : 14}
            {...props}
        >
            <path
                fill={mainColor}
                d="M6.999 9a.646.646 0 0 0 .475-.191.642.642 0 0 0 .191-.475.643.643 0 0 0-.192-.475A.648.648 0 0 0 7 7.667a.643.643 0 0 0-.475.192.648.648 0 0 0-.192.475c0 .189.064.347.192.475a.643.643 0 0 0 .475.192Zm-.667-2.666h1.333v-4H6.332v4Zm-6 7.333v-12c0-.366.13-.68.392-.941.261-.26.575-.392.941-.392h10.667c.367 0 .68.13.942.392.261.261.392.575.391.941v8c0 .367-.13.681-.391.942a1.28 1.28 0 0 1-.942.392H2.999L.332 13.667Zm2.1-4h9.9v-8H1.665v8.75l.767-.75Z"
            />
        </svg>
    );
}
 
export default SVGFeedback;
