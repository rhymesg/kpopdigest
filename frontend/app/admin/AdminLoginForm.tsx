'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

export function AdminLoginForm() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });

      if (!res.ok) {
        setError('Invalid password.');
        return;
      }

      router.refresh();
    } catch {
      setError('Login failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="admin-login" onSubmit={handleSubmit}>
      <label htmlFor="admin-password">Password</label>
      <input
        id="admin-password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        autoComplete="current-password"
        autoFocus
      />
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Signing in...' : 'Sign in'}
      </button>

      <style jsx>{`
        .admin-login {
          max-width: 360px;
          margin: 80px auto 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 24px;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }

        label {
          font-size: 13px;
          font-weight: 700;
          color: #475569;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }

        input {
          min-height: 42px;
          padding: 0 12px;
          border: 1px solid #cbd5e1;
          border-radius: 8px;
          font-size: 16px;
          color: #0f172a;
        }

        input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }

        p {
          margin: 0;
          color: #dc2626;
          font-size: 13px;
        }

        button {
          min-height: 42px;
          border: none;
          border-radius: 8px;
          background: #0f172a;
          color: #ffffff;
          font-weight: 700;
          cursor: pointer;
        }

        button:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
      `}</style>
    </form>
  );
}
