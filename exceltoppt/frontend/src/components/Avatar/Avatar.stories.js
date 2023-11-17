import { Avatar } from ".";

export default {
  title: "Components/Avatar",
  component: Avatar,
  argTypes: {
    variant: {
      options: ["rounded", "circular", "square"],
      control: { type: "select" },
    },
  },
};

export const Default = {
  args: {
    variant: "rounded",
    badge: true,
    icon: true,
    image: true,
    darkMode: true,
    className: {},
    text: "OP",
  },
};
