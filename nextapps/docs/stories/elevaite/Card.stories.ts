import type { Meta, StoryObj } from "@storybook/react";

import { Card, CardProps } from "@elevaite/ui";
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
    icon: slackImage.src,
    description:
      "Mauris in quam ut neque scelerisque ultrices at eget nisl. Praesent a risus in orci porttitor commodo.",
    title: "Slack Ingest",
    subtitle: "By Slack",
    iconAlt: "slack icon",
  },
};
