/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import React from "react";

export const Check = ({ className }) => {
  return (
    <svg
      className={`check ${className}`}
      fill="none"
      height="10"
      viewBox="0 0 10 10"
      width="10"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        className="path"
        d="M8.33341 2.5L3.75008 7.08333L1.66675 5"
        stroke="#70B758"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
};
