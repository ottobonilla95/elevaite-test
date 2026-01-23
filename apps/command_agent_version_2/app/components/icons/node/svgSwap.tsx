import type { SVGProps, JSX } from "react";


export default function SVGSwap(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 14 14"
            width={props.size ?? 14}
            height={props.size ?? 14}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12.5721 7.27632C12.3776 9.10324 11.3425 10.8153 9.62956 11.8042C6.78372 13.4472 3.14475 12.4722 1.50171 9.62634L1.32671 9.32323M0.737271 6.02609C0.931732 4.19916 1.96689 2.48715 3.67978 1.49822C6.52562 -0.144831 10.1646 0.830225 11.8076 3.67607L11.9826 3.97918M0.700195 10.8974L1.21263 8.98499L3.12507 9.49743M10.1847 3.80499L12.0971 4.31743L12.6095 2.40499"
            />
        </svg>
    );
}
