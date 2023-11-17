/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import PropTypes from "prop-types";
import React from "react";
import { useReducer } from "react";
import { XClose15 } from "../../icons/XClose15";
import { XClose7 } from "../../icons/XClose7";


export const ButtonCloseX = ({ size, color, theme, stateProp, className }) => {
  const [state, dispatch] = useReducer(reducer, {
    size: size || "lg",
    color: color || "primary",
    theme: theme || "light",
    state: stateProp || "default",
  });

  return (
    <div
      className={`button-close-x ${state.size} ${state.theme} ${state.state} ${state.color} ${className}`}
      onMouseLeave={() => {
        dispatch("mouse_leave");
      }}
      onMouseEnter={() => {
        dispatch("mouse_enter");
      }}
    >
      {state.size === "lg" && (
        <XClose15
          className="x-close"
          color={
            state.theme === "dark"
              ? "white"
              : state.color === "gray" && state.theme === "light" && ["default", "focused"].includes(state.state)
              ? "#667085"
              : state.state === "hover" && state.theme === "light" && state.color === "primary"
              ? "#7F56D9"
              : state.color === "gray" && state.theme === "light" && state.state === "hover"
              ? "#475467"
              : "#9E77ED"
          }
        />
      )}

      {["md", "sm"].includes(state.size) && (
        <XClose7
          className="x-close-7"
          color={
            state.theme === "dark"
              ? "white"
              : state.color === "gray" && state.theme === "light" && ["default", "focused"].includes(state.state)
              ? "#667085"
              : state.color === "primary" && state.theme === "light" && state.state === "hover"
              ? "#7F56D9"
              : state.color === "gray" && state.theme === "light" && state.state === "hover"
              ? "#475467"
              : "#9E77ED"
          }
        />
      )}
    </div>
  );
};

function reducer(state, action) {
  switch (action) {
    case "mouse_enter":
      return {
        ...state,
        state: "hover",
      };

    case "mouse_leave":
      return {
        ...state,
        state: "default",
      };
  }

  return state;
}

ButtonCloseX.propTypes = {
  size: PropTypes.oneOf(["md", "lg", "sm"]),
  color: PropTypes.oneOf(["primary", "gray"]),
  theme: PropTypes.oneOf(["dark", "light"]),
  stateProp: PropTypes.oneOf(["focused", "hover", "default"]),
};
