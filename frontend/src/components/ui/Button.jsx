import React from 'react';
import './Button.css';
import { Spinner } from './Spinner';

export function Button({
  children,
  variant = 'olive', // 'olive' | 'lemon' | 'secondary' | 'ghost' | 'danger'
  size = 'md',        // 'sm' | 'md' | 'lg'
  isBlock = false,
  isLoading = false,
  disabled = false,
  icon: Icon,
  iconRight: IconRight,
  className = '',
  type = 'button',
  onClick,
  ...props
}) {
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    isBlock ? 'btn-block' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || isLoading}
      onClick={onClick}
      {...props}
    >
      {isLoading && <Spinner size="sm" />}
      {!isLoading && Icon && <Icon size={size === 'sm' ? 16 : 18} />}
      <span>{children}</span>
      {!isLoading && IconRight && <IconRight size={size === 'sm' ? 16 : 18} />}
    </button>
  );
}

export default Button;
