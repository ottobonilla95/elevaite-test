import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGQuestionMark(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 9 14"
            width={props.size ? props.size : 9}
            height={props.size ? props.size * (14 / 9) : 14}
            {...props}
        >
            <path
                fill={mainColor}
                stroke={mainColor}
                strokeWidth={0.5}
                d="M2.27 4.171c0-.966.984-1.824 2.063-1.824 1.08 0 2.063.858 2.063 1.824 0 .476-.119.812-.313 1.103-.201.302-.487.563-.849.883l-.03.027-.008.008c-.71.628-1.661 1.471-1.661 3.129a.798.798 0 1 0 1.597 0c0-.468.117-.8.311-1.088.201-.3.487-.559.85-.881l.02-.018.009-.007c.714-.633 1.67-1.481 1.67-3.156 0-2.053-1.918-3.42-3.659-3.42-1.74 0-3.66 1.367-3.66 3.42a.798.798 0 0 0 1.598 0Zm2.063 9.079a1.085 1.085 0 1 0 0-2.17 1.085 1.085 0 0 0 0 2.17Z"
            />
        </svg>
    );
}
 
export default SVGQuestionMark;
