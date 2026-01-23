import type { SVGProps, JSX } from "react";


export default function SVGKnowledgeBase(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 14 16"
            width={props.size ? props.size * (14 / 16) : 14}
            height={props.size ?? 16}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.3 2.79995C13.3 3.95975 10.4793 4.89995 6.99995 4.89995C3.52056 4.89995 0.699951 3.95975 0.699951 2.79995M13.3 2.79995C13.3 1.64015 10.4793 0.699951 6.99995 0.699951C3.52056 0.699951 0.699951 1.64015 0.699951 2.79995M13.3 2.79995V12.6C13.3 13.762 10.5 14.7 6.99995 14.7C3.49995 14.7 0.699951 13.762 0.699951 12.6V2.79995M13.3 6.1041C13.3 7.2661 10.5 8.2041 6.99995 8.2041C3.49995 8.2041 0.699951 7.2661 0.699951 6.1041M13.3 9.40795C13.3 10.57 10.5 11.508 6.99995 11.508C3.49995 11.508 0.699951 10.57 0.699951 9.40795"
            />
        </svg>
    );
}
