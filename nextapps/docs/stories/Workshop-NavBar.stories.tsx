import type { Meta, StoryObj } from "@storybook/react";

import { NavBar } from "@elevaite/ui";

const meta = {
  title: "Workshop/NavBar",
  component: NavBar,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    breadcrumbItems: { control: "json" },
  },
} satisfies Meta<typeof NavBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Workshop: Story = {
  args: {
    breadcrumbItems: [{ label: "Workshop", link: "/workshop" }],
  },
};
