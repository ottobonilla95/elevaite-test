import type { Meta, StoryObj } from "@storybook/react";

import { WorkshopCard } from "@elevaite/ui";
import slackImage from "./assets/slack.svg";

const meta = {
  title: "Workshop/Card",
  component: WorkshopCard,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    description: { control: "text" },
  },
} satisfies Meta<typeof WorkshopCard>;

export default meta;
type Story = StoryObj<typeof meta>;

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
