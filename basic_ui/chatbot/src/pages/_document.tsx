import { Html, Head, Main, NextScript } from 'next/document';
import Image from 'next/image';
import paloAltoLogo from '../../public/palo_alto_logo.webp';
export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body>
        <div className='header-top'>
          <h1 className='logo-text'>elevAIte</h1>
        </div>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
