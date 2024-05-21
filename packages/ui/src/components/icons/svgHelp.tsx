import type { SVGProps } from "react"


function SVGHelp(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            height={props.size ? props.size : 20}
            {...props}
        >
            <path
                d="M7.57508 7.49999C7.771 6.94305 8.15771 6.47341 8.66671 6.17427C9.17571 5.87512 9.77416 5.76577 10.3561 5.86558C10.938 5.96539 11.4658 6.26793 11.846 6.7196C12.2262 7.17127 12.4343 7.74293 12.4334 8.33332C12.4334 9.99999 9.93342 10.8333 9.93342 10.8333M10.0001 14.1667H10.0084M18.3334 9.99999C18.3334 14.6024 14.6025 18.3333 10.0001 18.3333C5.39771 18.3333 1.66675 14.6024 1.66675 9.99999C1.66675 5.39762 5.39771 1.66666 10.0001 1.66666C14.6025 1.66666 18.3334 5.39762 18.3334 9.99999Z"
                stroke={mainColor}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
            />
        </svg>
    );
}
 
export default SVGHelp;
