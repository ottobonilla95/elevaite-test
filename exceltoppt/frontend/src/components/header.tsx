import React, { useState } from 'react';

function Header() {
  const [selectedButton, setSelectedButton] = useState('Apps'); // Set 'Func' as the default selected button

  const handleButtonClick = (buttonName: string) => {
    setSelectedButton(buttonName);
  };

  return (
    <div className="frame-2">
      <div className="frame-3">
        <img
          className="frame-1000004664"
          src="img/frame-1000004664.svg"
          alt="Frame 1000004664"
        />
        <img className="line-1 line" src="img/line-1.svg" alt="Line 1" />
        <ul className="mainmenu-button-list">
          <li>
            <button
              className={selectedButton === 'Dashboard' ? 'selected' : ''}
              onClick={() => handleButtonClick('Dashboard')}
            >
              Dashboard
            </button>
          </li>
          <li>
            <button
              className={selectedButton === 'KnowledgeBase' ? 'selected' : ''}
              onClick={() => handleButtonClick('KnowledgeBase')}
            >
              Knowledge Base
            </button>
          </li>
          <li>
            <button
              className={selectedButton === 'Function' ? 'selected' : ''}
              onClick={() => handleButtonClick('Function')}
            >
              Function
            </button>
          </li>
          <li>
            <button
              className={selectedButton === 'Apps' ? 'selected' : ''}
              onClick={() => handleButtonClick('Apps')}
            >
              Apps
            </button>
          </li>
          <li>
            <button
              className={selectedButton === 'Users' ? 'selected' : ''}
              onClick={() => handleButtonClick('Users')}
            >
              Users
            </button>
          </li>
          <li>
            <button
              className={selectedButton === 'Configuration' ? 'selected' : ''}
              onClick={() => handleButtonClick('Configuration')}
            >
              Configuration
            </button>
          </li>
        </ul>
      </div>
    </div>
  );
}

export default Header;
