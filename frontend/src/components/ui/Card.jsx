import React from 'react';
import './Card.css';

export function Card({
  children,
  className = '',
  variant = 'default', // 'default' | 'glass' | 'lemon-tint'
  isInteractive = false,
  onClick,
  ...props
}) {
  const classes = [
    'ui-card',
    variant !== 'default' ? `ui-card-${variant}` : '',
    isInteractive ? 'ui-card-interactive' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} onClick={onClick} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action, children, className = '' }) {
  return (
    <div className={`ui-card-header ${className}`}>
      <div>
        {title && <h3 className="ui-card-title">{title}</h3>}
        {subtitle && <p className="ui-card-subtitle">{subtitle}</p>}
        {children}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function CardBody({ children, className = '' }) {
  return <div className={`ui-card-body ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`ui-card-footer ${className}`}>{children}</div>;
}
