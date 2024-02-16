import type { SVGProps } from "react"


function SVGDocument(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 14 16"
            width={props.size ? props.size * (16/14) : 16}
            height={props.size ? props.size : 14}
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8.335 1.514v2.753c0 .374 0 .56.072.703a.667.667 0 0 0 .292.291c.142.073.329.073.702.073h2.754M9.668 8.667H4.335m5.333 2.667H4.335m1.333-5.333H4.335m4-4.667H4.868c-1.12 0-1.68 0-2.108.218a2 2 0 0 0-.874.874c-.218.428-.218.988-.218 2.108v6.933c0 1.12 0 1.68.218 2.108a2 2 0 0 0 .874.874c.428.218.988.218 2.108.218h4.267c1.12 0 1.68 0 2.108-.218a2 2 0 0 0 .874-.874c.218-.427.218-.988.218-2.108V5.334l-4-4Z"
            />
        </svg>
    );
}
 
export default SVGDocument;
