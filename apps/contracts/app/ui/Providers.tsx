import { ColorContextProvider } from "@repo/ui/contexts";


interface ProvidersProps {
  children?: React.ReactNode;
}


export default function Providers({ children }: ProvidersProps): JSX.Element {
  return (
    <ColorContextProvider>
      {children}
    </ColorContextProvider>
  );
}


