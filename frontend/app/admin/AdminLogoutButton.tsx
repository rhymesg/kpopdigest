'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function AdminLogoutButton() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const logout = async () => {
    setIsSubmitting(true);
    try {
      await fetch('/api/admin/logout', { method: 'POST' });
      router.refresh();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <button className="admin-logout" type="button" onClick={logout} disabled={isSubmitting}>
      {isSubmitting ? 'Signing out...' : 'Sign out'}

      <style jsx>{`
        .admin-logout {
          border: 1px solid #cbd5e1;
          background: #ffffff;
          color: #475569;
          border-radius: 999px;
          padding: 8px 14px;
          font-size: 13px;
          font-weight: 700;
          cursor: pointer;
        }

        .admin-logout:hover:not(:disabled) {
          border-color: #94a3b8;
          color: #0f172a;
        }

        .admin-logout:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
      `}</style>
    </button>
  );
}
