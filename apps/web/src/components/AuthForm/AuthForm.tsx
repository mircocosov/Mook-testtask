import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import styles from './AuthForm.module.scss';

type Props = { mode: 'login' | 'register' };

export function AuthForm({ mode }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(event.currentTarget);

    try {
      await api(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email: form.get('email'), password: form.get('password') }),
      });
      void router.push('/app');
    } catch {
      setError('Не удалось выполнить авторизацию');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <h1>{mode === 'login' ? 'Вход' : 'Регистрация'}</h1>
      <input name="email" type="email" required placeholder="Email" />
      <input name="password" type="password" minLength={8} required placeholder="Пароль" />
      {error ? <p className={styles.error}>{error}</p> : null}
      <button disabled={loading} type="submit">
        {loading ? '...' : mode === 'login' ? 'Войти' : 'Создать аккаунт'}
      </button>
    </form>
  );
}
