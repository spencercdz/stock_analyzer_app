import React from 'react';
import './Box.css';

const Box = ({ title, children, position }) => {
  return (
    <div className={`box ${position}`}>
      <h1>{title}</h1>
      {children}
    </div>
  );
};

export default Box; 