import { type InputHTMLAttributes, forwardRef } from "react";

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  ({ label, error, id, className = "", ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-xs font-medium uppercase tracking-wide text-paper-300">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={`rounded-lg border bg-ink-800 px-3.5 py-2.5 text-sm text-paper-100 placeholder:text-paper-300/50
            outline-none transition-colors focus:border-rose-500
            ${error ? "border-crimson-500" : "border-ink-600"} ${className}`}
          {...props}
        />
        {error && <span className="text-xs text-crimson-400">{error}</span>}
      </div>
    );
  }
);
InputField.displayName = "InputField";
