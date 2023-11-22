import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle } from '@fortawesome/free-solid-svg-icons';

interface ProgressbarProps {
  current?: number;
}

const Progressbar: React.FC<ProgressbarProps> = ({ current: initialCurrent = 1 }) => {
  //const steps: string[] = ["Upload Excel", "Review Manifest List", "Choose/Upload PPT Template", "View PPT"];
  const steps: string[] = ["Upload Excel", "Review Manifest List", "View PPT"];
  const [current, setCurrent] = useState(initialCurrent);

  return (
    <div className="flex justify-between relative">
      {steps.map((step, i) => (
        <div key={i} className="step-item">
          <div className="step" style={{ backgroundColor: current === i + 1 ? 'black' : 'white' }}>
            <FontAwesomeIcon icon={faCircle} className="circle-icon" style={{ fontSize: '0.5rem', color: current === i + 1 ? 'white' : 'grey' }} />
          </div>
          <p className={`text-${current === i + 1 ? 'black font-bold' : 'gray-500'} smallText`} style={{ whiteSpace: 'nowrap' }}>{step}</p>
        </div>
      ))}
    </div>
  );
};

export default Progressbar;
