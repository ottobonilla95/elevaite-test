/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import React from "react";


interface Props {
  className: any;
}

export const TypeAComment = ({ className }: Props): JSX.Element => {
  return (
    <div className={`type-a-comment ${className}`}>
      <div className="text-wrapper">Type a Comment...</div>
    </div>
  );
};
