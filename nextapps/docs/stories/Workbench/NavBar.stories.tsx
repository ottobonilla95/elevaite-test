import type { Meta, StoryObj } from "@storybook/react";

import { NavBar } from "@elevaite/ui";

const meta = {
  title: "Workbench/NavBar",
  component: NavBar,
  parameters: {
    layout: "fullscreen",
  },
  tags: ["autodocs"],
  argTypes: {
    breadcrumbItems: { control: "json" },
  },
} satisfies Meta<typeof NavBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Workbench: Story = {
  args: {
    breadcrumbItems: [{ label: "Workbench", link: "/Workbench" }],
    user: { icon: "..." },
  },
};
