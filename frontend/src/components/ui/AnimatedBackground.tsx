import React from 'react';
import { motion } from 'framer-motion';

interface AnimatedBackgroundProps {
  variant?: 'mesh' | 'particles' | 'waves' | 'aurora';
  intensity?: 'low' | 'medium' | 'high';
  className?: string;
}

export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({
  variant = 'mesh',
  intensity = 'medium',
  className = '',
}) => {
  const renderMesh = () => (
    <div className={`absolute inset-0 overflow-hidden ${className}`}>
      {/* Animated gradient mesh */}
      <motion.div
        className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-primary-500/20 via-accent-500/10 to-transparent rounded-full blur-3xl"
        animate={{
          x: [0, 100, 0],
          y: [0, -50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-accent-500/20 via-primary-500/10 to-transparent rounded-full blur-3xl"
        animate={{
          x: [0, -100, 0],
          y: [0, 50, 0],
          scale: [1.2, 1, 1.2],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
    </div>
  );

  const renderParticles = () => (
    <div className={`absolute inset-0 overflow-hidden ${className}`}>
      {Array.from({ length: 50 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-primary-400/30 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -100, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: Math.random() * 3 + 2,
            repeat: Infinity,
            delay: Math.random() * 2,
          }}
        />
      ))}
    </div>
  );

  const renderWaves = () => (
    <div className={`absolute inset-0 overflow-hidden ${className}`}>
      <svg className="absolute bottom-0 w-full h-32" viewBox="0 0 1200 120" preserveAspectRatio="none">
        <motion.path
          d="M0,60 C300,120 900,0 1200,60 L1200,120 L0,120 Z"
          fill="url(#waveGradient)"
          animate={{
            d: [
              "M0,60 C300,120 900,0 1200,60 L1200,120 L0,120 Z",
              "M0,80 C300,20 900,100 1200,40 L1200,120 L0,120 Z",
              "M0,60 C300,120 900,0 1200,60 L1200,120 L0,120 Z"
            ]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <defs>
          <linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(116, 109, 255, 0.3)" />
            <stop offset="100%" stopColor="rgba(116, 109, 255, 0.1)" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );

  const renderAurora = () => (
    <div className={`absolute inset-0 overflow-hidden ${className}`}>
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-primary-500/20 via-accent-500/20 to-success-500/20 blur-3xl"
        animate={{
          background: [
            "linear-gradient(45deg, rgba(116, 109, 255, 0.2), rgba(14, 165, 233, 0.2), rgba(16, 185, 129, 0.2))",
            "linear-gradient(45deg, rgba(14, 165, 233, 0.2), rgba(16, 185, 129, 0.2), rgba(245, 158, 11, 0.2))",
            "linear-gradient(45deg, rgba(16, 185, 129, 0.2), rgba(245, 158, 11, 0.2), rgba(116, 109, 255, 0.2))",
            "linear-gradient(45deg, rgba(116, 109, 255, 0.2), rgba(14, 165, 233, 0.2), rgba(16, 185, 129, 0.2))"
          ]
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
    </div>
  );

  const variants = {
    mesh: renderMesh,
    particles: renderParticles,
    waves: renderWaves,
    aurora: renderAurora,
  };

  return variants[variant]();
};