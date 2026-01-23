import type { JSX } from "react";
import type { SVGProps } from "react"


function SVGActionFlag(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 12 16"
            width={props.size ? props.size : 12}
            height={props.size ? props.size * (16/12) : 16}
            {...props}
        >
            <path
                fill={mainColor}
                d="M0 1.998c0-.17.066-.34.195-.47L.226 1.5l.05-.042c.039-.032.09-.072.156-.116.132-.088.319-.193.57-.293C1.506.846 2.258.667 3.333.667c1.13 0 2.065.374 2.877.7l.038.014C7.093 1.719 7.813 2 8.667 2c.925 0 1.506-.154 1.835-.286a1.787 1.787 0 0 0 .375-.2A.667.667 0 0 1 12 2v8c0 .17-.065.341-.195.471l-.001.001a1.975 1.975 0 0 1-.236.187 3.103 3.103 0 0 1-.57.293c-.504.202-1.256.381-2.331.381-1.13 0-2.065-.374-2.877-.7l-.038-.014C4.907 10.281 4.187 10 3.333 10c-.925 0-1.506.154-1.835.286-.064.025-.118.05-.165.073v4.308a.667.667 0 1 1-1.333 0V1.998Z"
            />
        </svg>
    );
}
 
export default SVGActionFlag;
