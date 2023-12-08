import * as React from "react";
import type { SVGProps } from "react";

function Workbench(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={24} width={24} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        clipRule="evenodd"
        d="m8.006 2.802.036.024L18.591 9.86c.305.203.588.392.805.567.227.183.495.437.649.808a2 2 0 0 1 0 1.532c-.154.371-.422.625-.649.808-.217.175-.5.364-.805.567L8.006 21.198c-.373.248-.708.472-.993.626-.285.155-.676.331-1.132.304a2 2 0 0 1-1.476-.79c-.276-.364-.346-.788-.376-1.11C4 19.905 4 19.502 4 19.054V4.946c0-.448 0-.851.03-1.174.029-.322.1-.745.375-1.11a2 2 0 0 1 1.476-.79c.456-.027.847.15 1.132.304.285.154.62.378.993.626Z"
        fill="currentColor"
        fillRule="evenodd"
      />
    </svg>
  );
}
export default Workbench;
