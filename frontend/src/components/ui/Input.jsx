import React from 'react';
import './Input.css';

export function Input({
  label,
  id,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  helperText,
  icon: Icon,
  endIcon: EndIcon,
  onEndIconClick,
  disabled = false,
  required = false,
  className = '',
  ...props
}) {
  const inputId = id || name;

  return (
    <div className={`input-wrapper ${className}`}>
      {label && (
        <label htmlFor={inputId} className="input-label">
          {label} {required && <span style={{ color: 'var(--color-error)' }}>*</span>}
        </label>
      )}
      <div className={`input-container ${error ? 'input-error' : ''}`}>
        {Icon && (
          <span className="input-icon-start">
            <Icon size={18} />
          </span>
        )}
        <input
          id={inputId}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className="input-field"
          {...props}
        />
        {EndIcon && (
          <span
            className="input-icon-end"
            onClick={onEndIconClick}
            role={onEndIconClick ? 'button' : undefined}
            tabIndex={onEndIconClick ? 0 : undefined}
          >
            <EndIcon size={18} />
          </span>
        )}
      </div>
      {(error || helperText) && (
        <p className={`input-helper ${error ? 'input-helper-error' : ''}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
}
