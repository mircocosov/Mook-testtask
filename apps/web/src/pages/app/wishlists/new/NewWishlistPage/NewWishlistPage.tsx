import { FormEvent } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import styles from './NewWishlistPage.module.scss';

export function NewWishlistPage() {
  const router = useRouter();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const created = await api<{ id: string }>('/wishlists', {
      method: 'POST',
      body: JSON.stringify({ title: form.get('title'), description: form.get('description') }),
    });
    await router.push(`/app/wishlists/${created.id}`);
  }

  return (
    <main className={styles.main}>
      <form className={styles.form} onSubmit={onSubmit}>
        <h1>Новый wishlist</h1>
        <input name="title" required placeholder="Название" />
        <textarea name="description" placeholder="Описание" />
        <button type="submit">Создать</button>
      </form>
    </main>
  );
}
