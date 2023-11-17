/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import PropTypes from "prop-types";
import React from "react";

export const Placeholder622 = ({ color = "#B42318", className }) => {
  return (
    <svg
      className={`placeholder-622 ${className}`}
      fill="none"
      height="20"
      viewBox="0 0 20 20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g className="g" clipPath="url(#clip0_2_7546)">
        <path
          className="path"
          d="M10 18.3334C14.6024 18.3334 18.3333 14.6024 18.3333 10C18.3333 5.39765 14.6024 1.66669 10 1.66669C5.39763 1.66669 1.66667 5.39765 1.66667 10C1.66667 14.6024 5.39763 18.3334 10 18.3334Z"
          stroke={color}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.66667"
        />
      </g>
      <defs className="defs">
        <clipPath className="clip-path" id="clip0_2_7546">
          <rect className="rect" fill="white" height="20" width="20" />
        </clipPath>
      </defs>
    </svg>
  );
};

Placeholder622.propTypes = {
  color: PropTypes.string,
};
