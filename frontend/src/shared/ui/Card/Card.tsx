import type { ReactNode } from 'react';
import styles from './Card.module.css';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
}

export function Card({ children, className = '', padding = 'md' }: CardProps) {
  return (
    <div className={`${styles.card} ${styles[padding]} ${className}`}>
      {children}
    </div>
  );
}
