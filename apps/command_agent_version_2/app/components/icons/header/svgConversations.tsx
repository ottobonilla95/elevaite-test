import type { SVGProps, JSX } from "react";


export default function SVGConversations(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            width={props.size ?? 16}
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
                d="M3.566 7.16A5.607 5.607 0 0 1 3.5 6.3C3.5 3.207 6.024.7 9.137.7c3.113 0 5.637 2.507 5.637 5.6 0 .699-.13 1.367-.364 1.984a2.057 2.057 0 0 0-.085.242.628.628 0 0 0-.016.135c-.002.052.006.108.02.22l.281 2.29c.03.248.046.372.005.462a.35.35 0 0 1-.18.176c-.091.039-.215.02-.462-.015l-2.23-.327c-.116-.017-.174-.026-.227-.026a.628.628 0 0 0-.14.015c-.052.011-.118.036-.251.086a5.657 5.657 0 0 1-2.85.293M4.643 14.7c2.075 0 3.758-1.724 3.758-3.85C8.4 8.724 6.717 7 4.642 7S.884 8.724.884 10.85c0 .427.068.839.194 1.223.053.162.08.243.088.299.009.058.01.09.007.149-.003.056-.017.12-.045.246L.7 14.7l2.096-.286c.115-.016.172-.024.222-.023.053 0 .08.003.132.013.049.01.122.036.268.087.383.135.795.209 1.224.209Z"
            />
        </svg>
    );
}