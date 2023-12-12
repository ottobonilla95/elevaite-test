import { useTypewriter } from "../hooks/useTypewriter";

export function Typewriter({
  texts,
  speed,
  stallCycles,
}: {
  texts: string[];
  speed?: number;
  stallCycles?: number;
}): JSX.Element {
  const displayText: string = useTypewriter(texts, speed, stallCycles);

  return <span className="ui-font-inter ui-line-clamp-2 ui-w-96">{displayText}</span>;
}
