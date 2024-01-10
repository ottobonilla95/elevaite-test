"use client";
import { createContext, useContext } from "react";

// STRUCTURE 

export interface ColorScheme {
  primary?: string;
  secondary?: string;
  tertiary?: string;
  highlight?: string;
  text?: string;
  secondaryText?: string;
  icon?: string;
  iconBorder?: string;
  hoverColor?: string;
  borderColor?: string;
  background?: string;  
}

export interface ColorContextStructure extends ColorScheme {
  getCSSVariablesColorsInjectionStyle: () => React.CSSProperties,
}

export const ColorContext = createContext<ColorContextStructure>({
  getCSSVariablesColorsInjectionStyle: () => { return {} },
});




// FUNCTIONS

function formatThemeToCSSVariables(theme: ColorScheme): React.CSSProperties {
  const style: Record<string, string> = Object.keys(theme).reduce((prev, curr) => {
    return {...prev, [`--ev-colors-${curr}`]: theme[curr as keyof ColorScheme]}
  }, {});
  return {
    ...style
  } as React.CSSProperties
}




// PROVIDER

interface ColorContextProviderProps {
  theme: ColorScheme,
  children: React.ReactNode;
}

export function ColorContextProvider(props: ColorContextProviderProps): React.ReactElement {

  function getCSSVariablesColorsInjectionStyle(): React.CSSProperties {
    return formatThemeToCSSVariables(props.theme);
  }

  return (
    <ColorContext.Provider
      value={ {
        ...props.theme,
        getCSSVariablesColorsInjectionStyle,
      } }
    >
      { props.children}
    </ColorContext.Provider>
  );
}

export function useColors(): ColorContextStructure {
  return useContext(ColorContext);
}