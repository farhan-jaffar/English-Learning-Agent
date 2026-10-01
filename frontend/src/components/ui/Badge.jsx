import React from 'react';

export function Badge({
  children,
  variant = 'lemon', // 'lemon' | 'olive' | 'muted' | 'success' | 'warning' | 'error'
  icon: Icon,
  className = '',
  ...props
}) {
  return (
    <span className={`badge badge-${variant} ${className}`} {...props}>
      {Icon && <Icon size={12} />}
      <span>{children}</span>
    </span>
  );
}

export default Badge;
