import type { SVGProps, JSX } from "react";


export default function SVGEvaluations(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 13 16"
            width={props.size ? props.size * (13 / 16) : 13}
            height={props.size ?? 16}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeOpacity={0.72}
                strokeWidth={1.4}
                d="M9.1 2.1c.65 0 .976 0 1.244.072a2.1 2.1 0 0 1 1.484 1.484c.072.268.072.593.072 1.244v6.44c0 1.176 0 1.764-.229 2.213a2.1 2.1 0 0 1-.918.918c-.449.229-1.037.229-2.213.229H4.06c-1.176 0-1.764 0-2.213-.229a2.1 2.1 0 0 1-.918-.918C.7 13.104.7 12.516.7 11.34V4.9c0-.651 0-.976.072-1.244a2.1 2.1 0 0 1 1.484-1.484C2.523 2.1 2.85 2.1 3.5 2.1m.7 7.7 1.4 1.4 3.15-3.15M4.62 3.5h3.36c.392 0 .588 0 .738-.076a.7.7 0 0 0 .306-.306c.076-.15.076-.346.076-.738v-.56c0-.392 0-.588-.076-.738a.7.7 0 0 0-.306-.306C8.568.7 8.372.7 7.98.7H4.62c-.392 0-.588 0-.738.076a.7.7 0 0 0-.306.306c-.076.15-.076.346-.076.738v.56c0 .392 0 .588.076.738a.7.7 0 0 0 .306.306c.15.076.346.076.738.076Z"
            />
        </svg>
    );
}