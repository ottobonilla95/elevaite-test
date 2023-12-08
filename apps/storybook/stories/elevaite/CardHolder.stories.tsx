import type { Meta, StoryObj } from "@storybook/react";
import { CardHolder } from "@repo/ui/components";

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

export const AppDrawer: Story = {
  args: { title: "ElevAIte for Support" },
};
