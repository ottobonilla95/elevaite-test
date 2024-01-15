import type { SVGProps } from "react"
import { useColors } from "../../../contexts/ColorContext";


function SVGMagnifyingGlass(props: SVGProps<SVGSVGElement>): JSX.Element {
    const theme = useColors();
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;
    else if (theme.icon) mainColor = theme.icon;

    return (
        <svg
          fill="none"
          height="20"
        //   style={{ color: theme.icon }}
          viewBox="0 0 20 20"
          width="20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M17.5 17.5L13.875 13.875M15.8333 9.16667C15.8333 12.8486 12.8486 15.8333 9.16667 15.8333C5.48477 15.8333 2.5 12.8486 2.5 9.16667C2.5 5.48477 5.48477 2.5 9.16667 2.5C12.8486 2.5 15.8333 5.48477 15.8333 9.16667Z"
            stroke={mainColor}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
        </svg>
    );
}
 
export default SVGMagnifyingGlass;
