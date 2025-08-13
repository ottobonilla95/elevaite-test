"use client";

import dayjs from "dayjs";
import { useEffect, useState } from "react";

interface UseElapsedTimeObject {
  elapsedTime: string;
  elapsedDays: string;
  elapsedHours: string;
  elapsedMinutes: string;
  elapsedSeconds: string;
}

export function useElapsedTime(
  startTime: string,
  endTime?: string
): UseElapsedTimeObject {
  const [elapsedTime, setElapsedTime] = useState<string>("");
  const [elapsedDays, setElapsedDays] = useState<string>("");
  const [elapsedHours, setElapsedHours] = useState<string>("");
  const [elapsedMinutes, setElapsedMinutes] = useState<string>("");
  const [elapsedSeconds, setElapsedSeconds] = useState<string>("");

  function resetValues(): void {
    setElapsedDays("");
    setElapsedHours("");
    setElapsedMinutes("");
    setElapsedSeconds("");
  }

  useEffect(() => {
    resetValues();
    setElapsedTime(getElapsedTime(startTime, endTime));
    if (!endTime) {
      const interval = setInterval(() => {
        setElapsedTime(getElapsedTime(startTime, endTime));
      }, 1000);
      return () => {
        clearInterval(interval);
      };
    }
  }, [endTime, startTime]);

  function getElapsedTime(start: string, end?: string): string {
    let duration = dayjs(end ?? undefined).diff(dayjs(start)) / 1000;
    const result: string[] = [];

    const days = Math.floor(duration / 86400);
    duration -= days * 86400;
    if (days > 0) {
      result.push(`${days.toString()}d`);
      setElapsedDays(days.toString());
    }

    const hours = Math.floor(duration / 3600) % 24;
    duration -= hours * 3600;
    if (days > 0 || hours > 0) {
      result.push(`${hours.toString().padStart(2, "0")}h`);
      setElapsedHours(hours.toString().padStart(2, "0"));
    }

    const minutes = Math.floor(duration / 60) % 60;
    duration -= minutes * 60;
    if (days > 0 || hours > 0 || minutes > 0) {
      result.push(`${minutes.toString().padStart(2, "0")}m`);
      setElapsedMinutes(minutes.toString().padStart(2, "0"));
    }

    const seconds = Math.floor(duration % 60);
    result.push(`${seconds.toString().padStart(2, "0")}s`);
    setElapsedSeconds(seconds.toString().padStart(2, "0"));

    return result.filter(Boolean).join(" ");
  }

  return {
    elapsedTime,
    elapsedDays,
    elapsedHours,
    elapsedMinutes,
    elapsedSeconds,
  };
}
