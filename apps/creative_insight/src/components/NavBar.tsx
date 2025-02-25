// components/Navbar.tsx

import { useState } from 'react';
import { Icons } from '../components/ui/icons';

const Navbar: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false); // State for dark mode toggle

  // Toggle between light and dark mode
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    // Toggle dark class on the body element
    document.body.classList.toggle('dark', !isDarkMode);
  };

  return (
    <nav className="flex justify-between items-center text-foreground pt-4 m-2">
      {/* Left Section */}
      <div className="flex items-center ml-4 p-4 mb-4 ">
      {/* <ElevaiteIcons.SVGFilter/> */}
      <img
          src={isDarkMode ? '/ElevAIte_dark.svg' : '/ElevAIte.svg'}
          alt="ElevAIte By Iopex Technologies"
        />
      </div>

      {/* Right Section */}
      <div>
        <button
          className="p-5 mr-10 text-foreground dark:text-primary hover:bg-muted dark:hover:bg-muted rounded-full"
          onClick={toggleTheme}
        >
          {isDarkMode ? <Icons.Sun/> : <Icons.Moon/> }
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
