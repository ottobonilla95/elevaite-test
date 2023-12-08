import type { Meta, StoryObj } from "@storybook/react";
import type { CardProps } from "@repo/ui/components";
import { Card } from "@repo/ui/components";
import slackImage from "../assets/slack.svg";

const meta = {
  title: "Elevaite/Card",
  component: Card,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<CardProps>;

export default meta;
type Story = StoryObj<CardProps>;

export const Slack: Story = {
  args: {
    icon: (slackImage as { src: string }).src,
    description:
      "Mauris in quam ut neque scelerisque ultrices at eget nisl. Praesent a risus in orci porttitor commodo.",
    title: "Slack Ingest",
    subtitle: "By Slack",
    iconAlt: "slack icon",
  },
};
