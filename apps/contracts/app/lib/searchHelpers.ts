import { getApplications } from "../../dummydata";

export function userSearchHelper(term: string): { key: string; link: string; label: string }[] {
  const applications = getApplications(process.env.NODE_ENV);
  const refs: { key: string; link: string; label: string }[] = [];
  applications.forEach((app) => {
    app.cards.forEach((card) => {
      refs.push({ key: (card.id?.toString() ?? card.iconAlt) ?? card.title, label: card.title, link: `#${card.id?.toString() ?? ""}` });
    });
  });
  return refs.filter((ref) => ref.label.toLowerCase().includes(term.toLowerCase()));
}

export function engineerSearchHelper(_term: string): { key: string; link: string; label: string }[] {
  return [];
}
