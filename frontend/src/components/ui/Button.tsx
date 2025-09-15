import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onAnimationStart' | 'onAnimationEnd' | 'onDragStart' | 'onDrag' | 'onDragEnd'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'neon';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  glow?: boolean;
  gradient?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  glow = false,
  gradient = false,
  className,
  children,
  disabled,
  ...props
}) => {
  const baseClasses = clsx(
    'relative inline-flex items-center justify-center font-medium rounded-xl',
    'transition-all duration-300 ease-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'overflow-hidden group',
    {
      // Sizes
      'px-3 py-2 text-sm': size === 'sm',
      'px-4 py-2.5 text-base': size === 'md',
      'px-6 py-3 text-lg': size === 'lg',
      'px-8 py-4 text-xl': size === 'xl',
      
      // Variants
      'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500': variant === 'primary' && !gradient,
      'bg-dark-800 text-dark-100 hover:bg-dark-700 focus:ring-dark-500 border border-dark-700': variant === 'secondary',
      'bg-transparent text-dark-300 hover:text-white hover:bg-dark-800 focus:ring-dark-500': variant === 'ghost',
      'bg-danger-600 text-white hover:bg-danger-700 focus:ring-danger-500': variant === 'danger',
      'bg-success-600 text-white hover:bg-success-700 focus:ring-success-500': variant === 'success',
      'bg-gradient-to-r from-primary-600 to-accent-600 text-white hover:from-primary-700 hover:to-accent-700': variant === 'neon' || gradient,
      
      // Glow effect
      'shadow-glow hover:shadow-glow-lg': glow,
      'shadow-neon': variant === 'neon',
    }
  );

  const shimmerClasses = 'absolute inset-0 -top-px bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 translate-x-[-100%] group-hover:animate-shimmer';

  return (
    <motion.button
      className={clsx(baseClasses, className)}
      disabled={disabled || loading}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      {...props}
    >
      {/* Shimmer effect */}
      <div className={shimmerClasses} />
      
      {/* Background gradient animation */}
      {gradient && (
        <div className="absolute inset-0 bg-gradient-to-r from-primary-600 via-accent-600 to-primary-600 bg-[length:200%_100%] animate-gradient opacity-80" />
      )}
      
      {/* Content */}
      <div className="relative flex items-center gap-2">
        {loading ? (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          <>
            {icon && iconPosition === 'left' && (
              <motion.span
                initial={{ rotate: 0 }}
                whileHover={{ rotate: 360 }}
                transition={{ duration: 0.3 }}
              >
                {icon}
              </motion.span>
            )}
            <span>{children}</span>
            {icon && iconPosition === 'right' && (
              <motion.span
                initial={{ rotate: 0 }}
                whileHover={{ rotate: 360 }}
                transition={{ duration: 0.3 }}
              >
                {icon}
              </motion.span>
            )}
          </>
        )}
      </div>
    </motion.button>
  );
};