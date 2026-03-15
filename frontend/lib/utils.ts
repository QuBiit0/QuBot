import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diff = now.getTime() - then.getTime();
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  
  return formatDate(date);
}

export const domainIcons: Record<string, string> = {
  TECH: '💻',
  FINANCE: '💰',
  MARKETING: '📢',
  HR: '👥',
  LEGAL: '⚖️',
  BUSINESS: '💼',
  PERSONAL: '🏠',
  OTHER: '🔧',
};

export const statusColors = {
  IDLE: 'bg-slate-500',
  WORKING: 'bg-green-500',
  ERROR: 'bg-red-500',
  OFFLINE: 'bg-gray-500',
};

export const priorityColors = {
  LOW: 'bg-slate-600',
  MEDIUM: 'bg-blue-600',
  HIGH: 'bg-yellow-600',
  CRITICAL: 'bg-red-600',
};

export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export const DOMAIN_CONFIG = {
  TECH: { label: 'Tecnología', icon: '💻', color: '#3b82f6' },
  FINANCE: { label: 'Finanzas', icon: '💰', color: '#22c55e' },
  MARKETING: { label: 'Marketing', icon: '📢', color: '#f59e0b' },
  HR: { label: 'Recursos Humanos', icon: '👥', color: '#8b5cf6' },
  LEGAL: { label: 'Legal', icon: '⚖️', color: '#ef4444' },
  BUSINESS: { label: 'Negocios', icon: '💼', color: '#06b6d4' },
  PERSONAL: { label: 'Personal', icon: '🏠', color: '#ec4899' },
  OTHER: { label: 'Otros', icon: '🔧', color: '#6b7280' },
};
