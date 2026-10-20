import type { ReactNode } from "react";

/** Small loading spinner with an accessible label. */
export function LoadingState({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-500" role="status">
      <span className="size-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      {label}
    </div>
  );
}

/** Error panel showing the server-provided message; never shows stale data. */
export function ErrorState({ title, message, onRetry }: { title: string; message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm" role="alert">
      <p className="font-semibold text-red-800">{title}</p>
      <p className="mt-1 text-red-700">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded bg-red-600 px-3 py-1.5 font-medium text-white hover:bg-red-700"
        >
          Retry
        </button>
      )}
    </div>
  );
}

/** Empty-state message for lists with no rows. */
export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500">{children}</div>;
}
