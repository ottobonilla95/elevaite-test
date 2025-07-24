"use client";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { type ColorScheme, DarkTheme, LightTheme, type ThemeObject, ThemeType } from "./themes";






// STATICS

const LOCAL_STORAGE_THEME = "elevaite_theme";

const defaultThemeList: ThemeObject[] = [
  { id: "darkTheme01", label: "Dark Theme", type: ThemeType.DARK, colors: DarkTheme },
  { id: "lightTheme01", label: "Light Theme", type: ThemeType.LIGHT, colors: LightTheme },
]





// STRUCTURE 


export interface ColorContextStructure extends ColorScheme {
  themesList: ThemeObject[];
  changeTheme: (themeId: string) => void;
}

export const ColorContext = createContext<ColorContextStructure>({
  themesList: [],
  changeTheme: () => { /** */ },
});




// FUNCTIONS


function setThemePropertiesToBody(theme: ColorScheme): void {
  (Object.keys(theme) as (keyof typeof theme)[]).forEach((themeKey) => {
    const propertyValue = theme[themeKey];
    if (propertyValue) {
      document.body.style.setProperty(
        `--ev-colors-${themeKey}`,
        propertyValue
      );
    }
  });


  // Set markdown colors specifically
  document.body.style.setProperty(`--markdown-heading-color`, theme.markdownHeading || '');
  document.body.style.setProperty(`--markdown-paragraph-color`, theme.markdownParagraph || '');
  document.body.style.setProperty(`--markdown-table-header-bg`, theme.markdownTableHeaderBg || '');
  document.body.style.setProperty(`--markdown-table-header-border`, theme.markdownTableHeaderBorder || '');
  document.body.style.setProperty(`--markdown-table-bg`, theme.markdownTableBg || '');
  document.body.style.setProperty(`--markdown-table-border`, theme.markdownTableBorder || '');

}





// PROVIDER

interface ColorContextProviderProps {
  children: React.ReactNode;
  themes?: ThemeObject[];
  hideDefaultThemes?: boolean;
}

export function ColorContextProvider({ children, themes, hideDefaultThemes }: ColorContextProviderProps): React.ReactElement {
  const combinedThemes = useMemo(() => {
    return (themes ?? []).concat(hideDefaultThemes ? [] : defaultThemeList);
  }, [themes, hideDefaultThemes]);
  const themesList = useMemo(() => combinedThemes, [combinedThemes]);
  const [selectedTheme, setSelectedTheme] = useState<ThemeObject>(combinedThemes[0]);

  useEffect(() => {
    const themeId = localStorage.getItem(LOCAL_STORAGE_THEME);
    if (themeId) changeTheme(themeId);
  }, []);

  useEffect(() => {
    setThemePropertiesToBody(selectedTheme.colors);
  }, [selectedTheme]);

  function changeTheme(themeId: string): void {
    const foundTheme = themesList.find(item => item.id === themeId);
    if (!foundTheme) return;
    localStorage.setItem(LOCAL_STORAGE_THEME, foundTheme.id);
    setSelectedTheme(foundTheme);
  }

  return (
    <ColorContext.Provider
      value={{
        ...selectedTheme.colors,
        themesList,
        changeTheme,
      }}
    >
      {children}
    </ColorContext.Provider>
  );
}

export function useThemes(): ColorContextStructure {
  return useContext(ColorContext);
}