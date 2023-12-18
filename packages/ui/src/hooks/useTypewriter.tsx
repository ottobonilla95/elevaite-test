import { useState, useEffect } from "react";

export const useTypewriter = (texts: string[], speed = 50, stallCycles = 0): string => {
  const [displayText, setDisplayText] = useState("");

  useEffect(() => {
    let i = 0;
    let j = 0;
    let k = 0;
    let isDeleting = false;
    let text = "";
    const typingInterval = setInterval(() => {
      text = texts[j];
      if (isDeleting) {
        setDisplayText(text.substring(0, i - 1));
        i--;
        if (i === 0) {
          isDeleting = false;
          k = 0;
          j++;
          if (j === texts.length) {
            j = 0;
          }
        }
      } else {
        if (i < text.length) {
          setDisplayText(text.substring(0, i + 1));
          i++;
        }
        if (i === text.length) {
          if (k === stallCycles) isDeleting = true;
          else k++;
        }
      }
    }, speed);

    return () => {
      clearInterval(typingInterval);
    };
  }, [texts, speed, stallCycles]);

  return displayText;
};
