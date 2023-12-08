import * as React from "react";
import type { SVGProps } from "react";

function Datasets(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={24} width={24} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        clipRule="evenodd"
        d="M1.106 11.553a1 1 0 0 1 1.341-.447L12 15.882l9.553-4.776a1 1 0 1 1 .894 1.788l-9.642 4.821-.026.014c-.093.047-.286.146-.502.186a1.5 1.5 0 0 1-.554 0c-.216-.04-.41-.139-.502-.186l-.026-.014-9.642-4.82a1 1 0 0 1-.447-1.342Z"
        fill="currentColor"
        fillRule="evenodd"
      />
      <path
        clipRule="evenodd"
        d="M1.106 16.553a1 1 0 0 1 1.341-.447L12 20.882l9.553-4.776a1 1 0 1 1 .894 1.788l-9.642 4.822-.026.012c-.093.048-.286.147-.502.187a1.5 1.5 0 0 1-.554 0c-.216-.04-.41-.139-.502-.186l-.026-.014-9.642-4.82a1 1 0 0 1-.447-1.342ZM11.723 1.085a1.5 1.5 0 0 1 .554 0 1.902 1.902 0 0 1 .528.2l9.642 4.82a1 1 0 0 1 0 1.79l-9.642 4.82-.026.014c-.093.047-.286.146-.502.186a1.5 1.5 0 0 1-.554 0c-.216-.04-.41-.139-.502-.186l-.026-.013-9.642-4.822a1 1 0 0 1 0-1.788l9.642-4.822.026-.013c.093-.047.286-.146.502-.186Z"
        fill="currentColor"
        fillRule="evenodd"
      />
    </svg>
  );
}
export default Datasets;
