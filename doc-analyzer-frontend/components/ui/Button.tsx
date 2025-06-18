// components/ui/Button.tsx
import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { clsx } from 'clsx';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  /** Button label or content */
  children?: React.ReactNode;
  /** Visual style variant */
  // ✅ THE FIX 1: Add 'outline' as a valid variant type
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  /** Size of the button */
  size?: 'sm' | 'md' | 'lg';
  /** Show a loading spinner and disable clicks */
  loading?: boolean;
  /** Optional icon to render before the children */
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className,
  disabled,
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900';

  const variants = {
    primary:
      'bg-primary-600 hover:bg-primary-700 text-white focus:ring-primary-500 shadow-lg hover:shadow-xl',
    secondary:
      'bg-dark-700 hover:bg-dark-600 text-white focus:ring-dark-500 border border-dark-600',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
    ghost: 'text-dark-300 hover:text-white hover:bg-dark-800 focus:ring-dark-500',
    // ✅ THE FIX 2: Add the styles for the new 'outline' variant
    outline:
      'border border-dark-600 text-dark-300 hover:bg-dark-800 hover:text-white focus:ring-dark-500',
  } as const;

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  } as const;

  const isDisabled = disabled || loading;

  return (
    <motion.button
      whileHover={!isDisabled ? { scale: 1.02 } : undefined}
      whileTap={!isDisabled ? { scale: 0.98 } : undefined}
      className={clsx(
        baseClasses,
        variants[variant],
        sizes[size],
        isDisabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <svg
          className="w-4 h-4 mr-2 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          />
        </svg>
      )}

      {!loading && icon && <span className="mr-2">{icon}</span>}

      {children}
    </motion.button>
  );
};
