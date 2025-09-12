import React from 'react';
import { motion } from 'framer-motion';

interface GlowingOrbProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'danger';
  intensity?: 'low' | 'medium' | 'high';
  animate?: boolean;
  className?: string;
}

export const GlowingOrb: React.FC<GlowingOrbProps> = ({
  size = 'md',
  color = 'primary',
  intensity = 'medium',
  animate = true,
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
    xl: 'w-32 h-32',
  };

  const colorClasses = {
    primary: 'bg-primary-500',
    accent: 'bg-accent-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    danger: 'bg-danger-500',
  };

  const glowClasses = {
    low: 'shadow-[0_0_20px_rgba(116,109,255,0.3)]',
    medium: 'shadow-[0_0_40px_rgba(116,109,255,0.5)]',
    high: 'shadow-[0_0_60px_rgba(116,109,255,0.7)]',
  };

  return (
    <motion.div
      className={`
        ${sizeClasses[size]}
        ${colorClasses[color]}
        ${glowClasses[intensity]}
        rounded-full
        ${animate ? 'animate-pulse' : ''}
        ${className}
      `}
      animate={animate ? {
        scale: [1, 1.1, 1],
        opacity: [0.7, 1, 0.7],
      } : {}}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
  );
};