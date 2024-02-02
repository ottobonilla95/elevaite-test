"use client";
import { useTypewriter } from "../hooks/useTypewriter";

export function Typewriter({
  texts,
  speed,
  stallCycles,
  className,
}: {
  texts: string[];
  speed?: number;
  stallCycles?: number;
  className?: string;
}): JSX.Element {
  const displayText: string = useTypewriter(texts, speed, stallCycles);

  return <span className={className}>{displayText}</span>;
}
