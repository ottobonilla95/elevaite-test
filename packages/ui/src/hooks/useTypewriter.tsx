import { useState, useEffect } from "react";

export const useTypewriter = (texts: string[], speed = 50): string => {
  const [displayText, setDisplayText] = useState("");

  useEffect(() => {
    let i = 0;
    let j = 0;
    let isDeleting = false;
    let text = "";
    const typingInterval = setInterval(() => {
      text = texts[j];
      if (isDeleting) {
        setDisplayText(text.substring(0, i - 1));
        i--;
        if (i === 0) {
          isDeleting = false;
          j++;
          if (j === texts.length) {
            j = 0;
          }
        }
      } else {
        setDisplayText(text.substring(0, i + 1));
        i++;
        if (i === text.length) {
          isDeleting = true;
        }
      }
    }, speed);

    return () => {
      clearInterval(typingInterval);
    };
  }, [texts, speed]);

  return displayText;
};
