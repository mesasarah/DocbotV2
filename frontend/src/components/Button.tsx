import { type ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  isLoading?: boolean;
}

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-rose-500 text-ink-950 hover:bg-rose-400 active:bg-rose-600 font-semibold",
  secondary: "bg-ink-700 text-paper-100 hover:bg-ink-600 border border-ink-600",
  ghost: "bg-transparent text-paper-200 hover:bg-ink-800 hover:text-paper-100",
  danger: "bg-transparent text-crimson-400 hover:bg-crimson-500/10 border border-crimson-500/40",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", isLoading, className = "", children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm
          transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed
          ${variantClasses[variant]} ${className}`}
        {...props}
      >
        {isLoading && (
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
