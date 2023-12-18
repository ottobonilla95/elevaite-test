
import PropTypes from "prop-types";
import React from "react";
import { Check } from "../../icons/Check";

export const Flow = ({ state, className }) => {
  return (
    <div className={`flow ${state} ${className}`}>
      {["active", "default"].includes(state) && <div className="ellipse" />}

      {state === "done" && <Check className="check-instance" />}
    </div>
  );
};

Flow.propTypes = {
  state: PropTypes.oneOf(["done", "active", "default"]),
};
