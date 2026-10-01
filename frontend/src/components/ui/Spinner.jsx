import React from 'react';
import './Spinner.css';

export function Spinner({ size = 'md', className = '', color }) {
  const sizeClass = `spinner-${size}`;
  const style = color ? { borderTopColor: color } : undefined;

  return (
    <div
      role="status"
      aria-label="Loading"
      className={`spinner ${sizeClass} ${className}`}
      style={style}
    />
  );
}

export default Spinner;
