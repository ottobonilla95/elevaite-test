import { ButtonCloseX } from ".";

export default {
  title: "Components/ButtonCloseX",
  component: ButtonCloseX,
  argTypes: {
    size: {
      options: ["md", "lg", "sm"],
      control: { type: "select" },
    },
    color: {
      options: ["primary", "gray"],
      control: { type: "select" },
    },
    theme: {
      options: ["dark", "light"],
      control: { type: "select" },
    },
    stateProp: {
      options: ["focused", "hover", "default"],
      control: { type: "select" },
    },
  },
};

export const Default = {
  args: {
    size: "md",
    color: "primary",
    theme: "dark",
    stateProp: "focused",
    className: {},
  },
};
