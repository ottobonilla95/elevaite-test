import type { Metadata } from "next";



export const metadata: Metadata = {
  title: "ElevAIte Chat",
  description: "ElevAIte's Chatbot, ready to answer your questions!",
};



export default function Layout({children,}: Readonly<{children: React.ReactNode;}>): JSX.Element {

  return (
    <>
      {children}
    </>
  );
}
