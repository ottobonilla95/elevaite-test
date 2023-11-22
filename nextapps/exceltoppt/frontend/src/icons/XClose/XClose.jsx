/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import React from "react";

export const XClose = ({ className , onClick}) => {
  return (
    <div onClick={onClick}>
      <svg
      className={`x-close ${className}`}
      fill="none"
      height="16"
      viewBox="0 0 17 16"
      width="17"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        className="path"
        d="M12.5 4L4.5 12M4.5 4L12.5 12"
        stroke="#666D80"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.33333"
      />
    </svg>
    </div>
  );
};
