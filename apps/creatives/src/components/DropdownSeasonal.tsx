// Dropdown.tsx

import React, { useState } from 'react';

const DropdownSeasonal: React.FC = () => {
  const options = [
    'New Years',
    'Valentines Day',
    'Easter',
    'July 4th',
    'Labor day',
    'Halloween',
    'Thanksgiving',
    'Christmas',
  ];

  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const handleOptionClick = (option: string) => {
    setSelectedOption(option);
    setIsOpen(false);
  };

  return (
    <div className="dropdown-containernew">
      <div className={`dropdownnew ${isOpen ? 'open' : ''}`} onClick={toggleDropdown}>
        <span>{selectedOption || 'Select an option'}</span>
        <span className="dropdown-arrow">&#9660;</span>
      </div>
      {isOpen && (
        <ul className="dropdown-menu-new">
          {options.map((option, index) => (
            <li
              key={index}
              className="dropdown-item-new"
              onClick={() => handleOptionClick(option)}
            >
              {option}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DropdownSeasonal;
