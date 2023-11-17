import { Flow } from ".";

export default {
  title: "Components/Flow",
  component: Flow,
  argTypes: {
    state: {
      options: ["done", "active", "default"],
      control: { type: "select" },
    },
  },
};

export const Default = {
  args: {
    state: "done",
    className: {},
  },
};
