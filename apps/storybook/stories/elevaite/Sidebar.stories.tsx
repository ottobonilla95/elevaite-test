import type { Meta, StoryObj } from "@storybook/react";
import { Sidebar, ElevaiteIcons } from "@repo/ui/components";

const meta = {
  title: "Elevaite/Sidebar",
  component: Sidebar,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof Sidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

const sidebarIcons: {
  linkLocation: string;
  Icon: React.ReactNode;
}[] = [
  { Icon: <ElevaiteIcons.Datasets />, linkLocation: "/datasets" },
  { Icon: <ElevaiteIcons.WorkersQueues />, linkLocation: "/workers_queues" },
  { Icon: <ElevaiteIcons.Models />, linkLocation: "/models" },
  { Icon: <ElevaiteIcons.Workbench />, linkLocation: "/workbench" },
];

export const Workbench: Story = {
  args: {
    sidebarIcons,
  },
  parameters: {
    nextjs: {
      appDirectory: true,
    },
  },
};
