import { ColorContextProvider } from "@repo/ui/contexts";
import { SessionWrapper } from "./SessionWrapper";


interface ProvidersProps {
  children?: React.ReactNode;
}


export default function Providers({ children }: ProvidersProps): JSX.Element {
  return (
    <SessionWrapper>
          <ColorContextProvider>
            {children}
          </ColorContextProvider>
    </SessionWrapper>
  );
}


