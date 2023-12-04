import type { Meta, StoryObj } from "@storybook/react";

import { Searchbar } from "@elevaite/ui";

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
  const promise: Promise<{ key: string; link: string; label: string }[]> = new Promise((resolve, reject) => {
    const refs: { key: string; link: string; label: string }[] = [
      { key: "supportBot", label: "Support Bot", link: "#supportBot" },
      { key: "deckBuilder", label: "AI Deck Builder", link: "#deckBuilder" },
      { key: "insights", label: "Insights", link: "#insights" },
      { key: "campaignBuilder", label: "Campaign Builder", link: "#campaignBuilder" },
    ];
    resolve(refs.filter((ref) => ref.label.toLowerCase().includes(term.toLowerCase())));
  });
  promise.then((res) => {
    results = res;
  });
}

export const Workbench: Story = {
  args: {
    handleInput: handleSearchInput,
    results: results,
  },
  parameters: {
    nextjs: {
      appDirectory: true,
    },
  },
};
