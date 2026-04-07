import styles from './UI.module.css';

export function Button({ children, variant = 'primary', size = 'md', loading, disabled, fullWidth, onClick, type = 'button', ...props }) {
  return (
    <button
      type={type}
      className={[styles.btn, styles[variant], styles[size], fullWidth && styles.full, loading && styles.loading].filter(Boolean).join(' ')}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? <span className={styles.spinner} /> : children}
    </button>
  );
}

export function Input({ label, error, helper, ...props }) {
  return (
    <div className={styles.field}>
      {label && <label className={styles.label}>{label}</label>}
      <input className={[styles.input, error && styles.inputError].filter(Boolean).join(' ')} {...props} />
      {error && <p className={styles.error}>{error}</p>}
      {helper && !error && <p className={styles.helper}>{helper}</p>}
    </div>
  );
}

export function Select({ label, error, children, ...props }) {
  return (
    <div className={styles.field}>
      {label && <label className={styles.label}>{label}</label>}
      <select className={[styles.input, error && styles.inputError].filter(Boolean).join(' ')} {...props}>
        {children}
      </select>
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}

export function Spinner({ size = 24, center }) {
  return (
    <div style={center ? { display: 'flex', justifyContent: 'center', padding: '48px' } : {}}>
      <div className={styles.spinnerLg} style={{ width: size, height: size }} />
    </div>
  );
}

export function Modal({ open, onClose, title, children, width = 480 }) {
  if (!open) return null;
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} style={{ maxWidth: width }} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3>{title}</h3>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>
        <div className={styles.modalBody}>{children}</div>
      </div>
    </div>
  );
}

export function Toast({ message, type = 'info', onClose }) {
  return (
    <div className={[styles.toast, styles[`toast-${type}`]].join(' ')}>
      <span>{message}</span>
      <button onClick={onClose}>×</button>
    </div>
  );
}

export function EmptyState({ icon, title, subtitle }) {
  return (
    <div className={styles.empty}>
      {icon && <div className={styles.emptyIcon}>{icon}</div>}
      <h3>{title}</h3>
      {subtitle && <p>{subtitle}</p>}
    </div>
  );
}

export function StatusBadge({ status }) {
  const map = {
    pending: 'yellow',
    accepted: 'blue',
    preparing: 'blue',
    delivering: 'accent',
    delivered: 'green',
    cancelled: 'red',
    rejected: 'red',
    waiting_for_driver: 'yellow',
    available: 'green',
    unavailable: 'gray',
  };
  const color = map[status] || 'gray';
  return <span className={`badge badge-${color}`}>{status?.replace(/_/g, ' ')}</span>;
}
