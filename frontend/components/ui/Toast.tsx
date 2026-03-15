'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastProps extends Toast {
  onDismiss: (id: string) => void;
}

const icons = {
  success: Check,
  error: AlertCircle,
  info: Info,
  warning: AlertCircle,
};

const styles = {
  success: 'bg-green-500/10 border-green-500/30 text-green-400',
  error: 'bg-red-500/10 border-red-500/30 text-red-400',
  info: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
  warning: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
};

function ToastItem({ id, type, title, message, duration = 5000, onDismiss }: ToastProps) {
  const Icon = icons[type];

  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(id);
    }, duration);

    return () => clearTimeout(timer);
  }, [id, duration, onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={cn(
        'flex items-start gap-3 p-4 rounded-xl border shadow-lg min-w-[300px] max-w-[400px]',
        styles[type]
      )}
    >
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <h4 className="font-medium">{title}</h4>
        {message && <p className="text-sm opacity-80 mt-1">{message}</p>}
      </div>
      <button
        onClick={() => onDismiss(id)}
        className="opacity-60 hover:opacity-100 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
}

// Global toast state
let listeners: ((toasts: Toast[]) => void)[] = [];
let toasts: Toast[] = [];

const notifyListeners = () => {
  listeners.forEach((listener) => listener(toasts));
};

export const toast = {
  show: (type: ToastType, title: string, message?: string, duration?: number) => {
    const id = Math.random().toString(36).substring(2, 9);
    toasts = [...toasts, { id, type, title, message, duration }];
    notifyListeners();
    return id;
  },
  success: (title: string, message?: string, duration?: number) =>
    toast.show('success', title, message, duration),
  error: (title: string, message?: string, duration?: number) =>
    toast.show('error', title, message, duration),
  info: (title: string, message?: string, duration?: number) =>
    toast.show('info', title, message, duration),
  warning: (title: string, message?: string, duration?: number) =>
    toast.show('warning', title, message, duration),
  dismiss: (id: string) => {
    toasts = toasts.filter((t) => t.id !== id);
    notifyListeners();
  },
};

export function ToastContainer() {
  const [localToasts, setLocalToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (newToasts: Toast[]) => setLocalToasts(newToasts);
    listeners.push(listener);
    return () => {
      listeners = listeners.filter((l) => l !== listener);
    };
  }, []);

  const handleDismiss = (id: string) => {
    toast.dismiss(id);
  };

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {localToasts.map((t) => (
          <ToastItem key={t.id} {...t} onDismiss={handleDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
}
