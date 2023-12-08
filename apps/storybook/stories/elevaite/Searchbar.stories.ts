import type { Meta, StoryObj } from "@storybook/react";
import { Searchbar } from "@repo/ui/components";

const meta = {
  title: "Elevaite/SearchBar",
  component: Searchbar,
  parameters: {
    layout: "fullscreen",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof Searchbar>;

export default meta;
type Story = StoryObj<typeof meta>;

let results: { key: string; link: string; label: string }[] = [];

function handleSearchInput(term: string) {
  const refs: { key: string; link: string; label: string }[] = [
    { key: "supportBot", label: "Support Bot", link: "#supportBot" },
    { key: "deckBuilder", label: "AI Deck Builder", link: "#deckBuilder" },
    { key: "insights", label: "Insights", link: "#insights" },
    { key: "campaignBuilder", label: "Campaign Builder", link: "#campaignBuilder" },
  ];
  results = refs.filter((ref) => ref.label.toLowerCase().includes(term.toLowerCase()));
}

export const Workbench: Story = {
  args: {
    handleInput: handleSearchInput,
    results,
    resultsTopOffset: "0px",
  },
  parameters: {
    nextjs: {
      appDirectory: true,
    },
  },
};
