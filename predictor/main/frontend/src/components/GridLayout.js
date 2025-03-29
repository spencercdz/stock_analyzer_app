import React from 'react';
import './GridLayout.css';

const GridLayout = ({ children }) => {
  return (
    <div className="container">
      <div className="grid-container">
        {children}
      </div>
    </div>
  );
};

export default GridLayout; 