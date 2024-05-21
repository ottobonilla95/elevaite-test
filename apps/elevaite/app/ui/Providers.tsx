import { ColorContextProvider } from "@repo/ui/contexts";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import { SessionWrapper } from "./SessionWrapper";


interface ProvidersProps {
  children?: React.ReactNode;
}


export default function Providers({ children }: ProvidersProps): JSX.Element {
  return (
    <SessionWrapper>
      <RolesContextProvider>
          <ColorContextProvider>
            {children}
          </ColorContextProvider>
      </RolesContextProvider>
    </SessionWrapper>
  );
}


