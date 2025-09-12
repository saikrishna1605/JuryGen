import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  gradient?: boolean;
  blur?: boolean;
  neon?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hover = true,
  glow = false,
  gradient = false,
  blur = false,
  neon = false,
  onClick,
}) => {
  const baseClasses = clsx(
    'relative rounded-2xl border transition-all duration-300',
    {
      // Base styles
      'bg-dark-800/50 border-dark-700': !gradient && !blur,
      'backdrop-blur-xl bg-dark-800/30 border-dark-600/50': blur,
      'bg-gradient-to-br from-dark-800/80 to-dark-900/80 border-primary-500/30': gradient,
      
      // Interactive styles
      'cursor-pointer': onClick,
      'hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/10': hover && !neon,
      'hover:shadow-neon hover:border-primary-400': neon,
      
      // Glow effect
      'shadow-glow': glow,
    }
  );

  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    hover: hover ? { y: -5, scale: 1.02 } : {},
  };

  return (
    <motion.div
      className={clsx(baseClasses, className)}
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      onClick={onClick}
    >
      {/* Animated border gradient */}
      {neon && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary-500 via-accent-500 to-primary-500 bg-[length:200%_100%] animate-gradient opacity-50 blur-sm -z-10" />
      )}
      
      {/* Inner glow */}
      {glow && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary-500/10 to-transparent" />
      )}
      
      {children}
    </motion.div>
  );
};