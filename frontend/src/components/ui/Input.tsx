import React from 'react';
import { Search, X, AlertCircle } from 'lucide-react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  isMonospace?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, required, isMonospace, className = '', id, ...props }, ref) => {
    const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <div className="form-group">
        {label && (
          <label htmlFor={inputId} className="form-label">
            <span>
              {label}
              {required && <span className="form-label-required">*</span>}
            </span>
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`input-control ${isMonospace ? 'font-mono' : ''} ${
            error ? 'has-error' : ''
          } ${className}`}
          {...props}
        />
        {hint && !error && <div className="form-hint">{hint}</div>}
        {error && (
          <div className="form-error" role="alert">
            <AlertCircle size={11} />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

export interface SearchBarProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({ value, onChange, onClear, placeholder = 'Search...', className = '', ...props }) => {
  return (
    <div className={`search-bar-wrap ${className}`}>
      <Search size={14} className="search-bar-icon" />
      <input
        type="text"
        className="input-control search-bar-input"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        {...props}
      />
      {value && onClear && (
        <button
          type="button"
          className="search-clear-btn"
          onClick={onClear}
          aria-label="Clear search"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
};

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  isMonospace?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, required, isMonospace, className = '', id, ...props }, ref) => {
    const areaId = id || (label ? `textarea-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <div className="form-group">
        {label && (
          <label htmlFor={areaId} className="form-label">
            <span>
              {label}
              {required && <span className="form-label-required">*</span>}
            </span>
          </label>
        )}
        <textarea
          ref={ref}
          id={areaId}
          className={`textarea-control ${isMonospace ? 'font-mono' : ''} ${
            error ? 'has-error' : ''
          } ${className}`}
          {...props}
        />
        {hint && !error && <div className="form-hint">{hint}</div>}
        {error && (
          <div className="form-error" role="alert">
            <AlertCircle size={11} />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';
