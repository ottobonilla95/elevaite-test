import { getApplications } from "../../dummydata";

export function userSearchHelper(term: string): { key: string; link: string; label: string }[] {
  const applications = getApplications(process.env.NODE_ENV);
  const refs: { key: string; link: string; label: string }[] = [];
  applications.forEach((app) => {
    app.cards.forEach((card) => {
      refs.push({ key: card.id || card.iconAlt, label: card.title, link: `#${card.id}` });
    });
  });
  return refs.filter((ref) => ref.label.toLowerCase().includes(term.toLowerCase()));
}

export function engineerSearchHelper(_term: string): { key: string; link: string; label: string }[] {
  return [];
}
