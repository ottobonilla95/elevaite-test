import type { Meta, StoryObj } from "@storybook/react";

import { Sidebar, ElevaiteIcons, SidebarIconProps, CardHolder } from "@elevaite/ui";

const meta = {
  title: "Elevaite/CardHolder",
  component: CardHolder,
  parameters: {
    layout: "fullscreen",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof CardHolder>;

export default meta;
type Story = StoryObj<typeof meta>;

const sidebarIcons: SidebarIconProps[] = [
  { Icon: <ElevaiteIcons.Datasets />, linkLocation: "/datasets" },
  { Icon: <ElevaiteIcons.WorkersQueues />, linkLocation: "/workers_queues" },
  { Icon: <ElevaiteIcons.Models />, linkLocation: "/models" },
  { Icon: <ElevaiteIcons.Workbench />, linkLocation: "/workbench" },
];

export const AppDrawer: Story = {
  args: { title: "ElevAIte for Support" },
};
