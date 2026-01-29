// ElevAIte Main Application Layout
import { Inter } from "next/font/google";
import "./layout.scss";
import Providers from "./ui/Providers";


const font = Inter({ subsets: ["latin"] });


interface RootLayoutProps {
    children: React.ReactNode
}

export default function RootLayout({children}: RootLayoutProps): JSX.Element {

    return (
        <html lang="en">
            <body className={font.className}>
                <Providers>
                    {children}
                </Providers>
            </body>
        </html>
    );
}