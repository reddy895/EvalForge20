import React from 'react';
import { Search, X } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, className = '', id, ...props }, ref) => {
    const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-[#F5F0E7]/90 tracking-wide">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`h-10 px-4 rounded-xl bg-[#191A18] border border-[#41413B] text-[#F5F0E7] placeholder-[#78766F] text-sm outline-none transition-all duration-150 focus:border-[#D9823B] focus:ring-1 focus:ring-[#D9823B] disabled:opacity-50 disabled:cursor-not-allowed ${
            error ? 'border-[#D66D60]' : ''
          } ${className}`}
          {...props}
        />
        {hint && !error && <span className="text-[11px] text-[#A6A49D]">{hint}</span>}
        {error && <span className="text-[11px] text-[#D66D60]">{error}</span>}
      </div>
    );
  }
);
Input.displayName = 'Input';

export interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  onClear,
  placeholder = 'Search models by name, architecture, or capability...',
  className = '',
  ...props
}) => {
  return (
    <div className={`relative flex items-center w-full ${className}`}>
      <Search size={16} className="absolute left-4 text-[#A6A49D] pointer-events-none" />
      <input
        type="text"
        className="w-full h-11 pl-11 pr-10 rounded-full bg-[#191A18] border border-[#41413B] text-[#F5F0E7] placeholder-[#78766F] text-sm outline-none transition-all duration-150 focus:border-[#D9823B] focus:ring-1 focus:ring-[#D9823B]"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        {...props}
      />
      {value && onClear && (
        <button
          type="button"
          onClick={onClear}
          className="absolute right-3.5 p-1 text-[#A6A49D] hover:text-[#F5F0E7] rounded-full hover:bg-white/5 transition-colors cursor-pointer"
          aria-label="Clear search"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
};

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options?: SelectOption[];
}

export const Select: React.FC<SelectProps> = ({ label, options, children, className = '', id, ...props }) => {
  const selectId = id || (label ? `select-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={selectId} className="text-xs font-medium text-[#F5F0E7]/90 tracking-wide">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`h-10 px-4 pr-9 rounded-xl bg-[#191A18] border border-[#41413B] text-[#F5F0E7] text-sm outline-none cursor-pointer transition-all duration-150 focus:border-[#D9823B] focus:ring-1 focus:ring-[#D9823B] appearance-none bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%23A6A49D%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3e%3cpolyline points=%276 9 12 15 18 9%27%3e%3c/polyline%3e%3c/svg%3e')] bg-no-repeat bg-[right_12px_center] bg-[length:14px_14px] ${className}`}
        {...props}
      >
        {options
          ? options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-[#191A18] text-[#F5F0E7]">
                {opt.label}
              </option>
            ))
          : children}
      </select>
    </div>
  );
};
