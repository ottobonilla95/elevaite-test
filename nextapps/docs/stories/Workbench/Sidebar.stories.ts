import type { Meta, StoryObj } from "@storybook/react";

import { Sidebar, ElevaiteIcons } from "@elevaite/ui";
import elevaiteImage from "./assets/elevaiteLogo.svg";

const meta = {
  title: "Workbench/Sidebar",
  component: Sidebar,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof Sidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Workbench: Story = {
  args: {
    sidebarIcons: [
      { Icon: ElevaiteIcons.Datasets, linkLocations: "", selected: false },
      { Icon: ElevaiteIcons.WorkersQueues, linkLocations: "", selected: false },
      { Icon: ElevaiteIcons.Models, linkLocations: "", selected: false },
      { Icon: ElevaiteIcons.Workbench, linkLocations: "", selected: true },
    ],
    Logo: ElevaiteIcons.Logo,
  },
};
