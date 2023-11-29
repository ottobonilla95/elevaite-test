import type { Meta, StoryObj } from "@storybook/react";

import { WorkbenchCard, WorkbenchCardProps } from "@elevaite/ui";
import slackImage from "../assets/slack.svg";

const meta = {
  title: "Workbench/Card",
  component: WorkbenchCard,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<WorkbenchCardProps>;

export default meta;
type Story = StoryObj<WorkbenchCardProps>;

export const Slack: Story = {
  args: {
    icon: slackImage.src,
    description:
      "Mauris in quam ut neque scelerisque ultrices at eget nisl. Praesent a risus in orci porttitor commodo.",
    title: "Slack Ingest",
    subtitle: "By Slack",
    iconAlt: "slack icon",
  },
};
