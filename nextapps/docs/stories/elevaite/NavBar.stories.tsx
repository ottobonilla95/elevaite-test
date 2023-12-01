import type { Meta, StoryObj } from "@storybook/react";

import { NavBar } from "@elevaite/ui";

const meta = {
  title: "Elevaite/NavBar",
  component: NavBar,
  parameters: {
    layout: "fullscreen",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof NavBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Workbench: Story = {
  args: {
    breadcrumbLabels: { workbench: { label: "Workbench", link: "/Workbench" } },
    user: { icon: "..." },
  },
  parameters: {
    nextjs: {
      appDirectory: true,
    },
  },
};
