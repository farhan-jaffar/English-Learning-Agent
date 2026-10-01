import React from 'react';
import { useUiStore } from '../../stores/uiStore';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import './Toast.css';

const ICONS = {
  success: <CheckCircle2 size={20} color="var(--color-success)" />,
  error: <AlertCircle size={20} color="var(--color-error)" />,
  info: <Info size={20} color="var(--color-info)" />,
  warning: <AlertTriangle size={20} color="var(--color-warning)" />,
};

export function ToastContainer() {
  const { toasts, removeToast } = useUiStore();

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast-item toast-item-${toast.type}`}>
          <div className="toast-icon">{ICONS[toast.type] || ICONS.info}</div>
          <div className="toast-content">
            {toast.title && <h5 className="toast-title">{toast.title}</h5>}
            <p className="toast-message">{toast.message}</p>
          </div>
          <button
            type="button"
            className="toast-close-btn"
            onClick={() => removeToast(toast.id)}
            aria-label="Close notification"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
