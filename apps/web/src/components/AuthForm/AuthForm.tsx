import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import styles from './AuthForm.module.scss';

type Props = { mode: 'login' | 'register' };

export function AuthForm({ mode }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [logoutLoading, setLogoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onLogout() {
    setLogoutLoading(true);
    setError(null);

    try {
      await api('/auth/logout', { method: 'POST' });
      void router.push('/');
    } catch {
      setError('Не удалось выйти из аккаунта');
    } finally {
      setLogoutLoading(false);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(event.currentTarget);

    try {
      const body = {
        ...(mode === 'register' ? { username: `${form.get('username') || ''}`.trim() } : {}),
        email: `${form.get('email') || ''}`.trim(),
        password: `${form.get('password') || ''}`,
      };

      await api(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      void router.push('/app');
    } catch (requestError) {
      if (requestError instanceof Error && requestError.message) {
        setError(requestError.message);
      } else {
        setError('Не удалось выполнить авторизацию');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <div className={styles.header}>
        <h1>{mode === 'login' ? 'Вход' : 'Регистрация'}</h1>
        <button className={styles.logout} disabled={logoutLoading} onClick={onLogout} type="button">
          {logoutLoading ? '...' : 'Выйти'}
        </button>
      </div>

      {mode === 'register' ? <input name="username" minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" required placeholder="Username" /> : null}
      <input name="email" type="email" required placeholder="Email" />
      <input name="password" type="password" minLength={8} required placeholder="Пароль" />
      {error ? <p className={styles.error}>{error}</p> : null}
      <button disabled={loading} type="submit">
        {loading ? '...' : mode === 'login' ? 'Войти' : 'Создать аккаунт'}
      </button>
    </form>
  );
}
