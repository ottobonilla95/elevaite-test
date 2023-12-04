import type { Meta, StoryObj } from "@storybook/react";

import { NavBar } from "@elevaite/ui";

const meta = {
  title: "Elevaite/NavBar",
  component: NavBar,
  parameters: {
    layout: "fullscreen",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof NavBar>;

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
    breadcrumbLabels: { workbench: { label: "Workbench", link: "/Workbench" } },
    user: { icon: "..." },
    handleSearchInput: handleSearchInput,
    searchResults: results,
  },
  parameters: {
    nextjs: {
      appDirectory: true,
    },
  },
};
