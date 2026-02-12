import { useEffect, useMemo, useState } from 'react';
import { API, api } from '@/lib/api';
import { ItemCard, PublicItem } from '@/components/ItemCard';
import styles from './WishlistView.module.scss';

type WishlistData = {
  id: string;
  title: string;
  description?: string;
  public_id: string;
  items: PublicItem[];
};

type Props = {
  mode: 'owner' | 'public';
  idOrPublicId: string;
};

export function WishlistView({ mode, idOrPublicId }: Props) {
  const [data, setData] = useState<WishlistData | null>(null);
  const path = useMemo(
    () => (mode === 'owner' ? `/wishlists/${idOrPublicId}` : `/public/w/${idOrPublicId}`),
    [mode, idOrPublicId],
  );

  const load = () => api<WishlistData>(path).then(setData).catch(() => setData(null));

  useEffect(() => {
    void load();
  }, [path]);

  useEffect(() => {
    if (!data?.public_id) return;
    const ws = new WebSocket(`${API.replace('http', 'ws')}/ws/wishlists/${data.public_id}`);
    ws.onmessage = () => void load();
    const poll = window.setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        void load();
      }
    }, 15000);

    return () => {
      window.clearInterval(poll);
      ws.close();
    };
  }, [data?.public_id]);

  if (!data) return <main className={styles.main}>Загрузка...</main>;

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1>{data.title}</h1>
        <p>{data.description}</p>
      </header>

      {data.items.length === 0 ? (
        <div className={styles.empty}>
          {mode === 'owner'
            ? 'Список пуст. Добавьте первый подарок.'
            : 'Лист еще не заполнен, проверьте позже.'}
        </div>
      ) : (
        <section className={styles.grid}>
          {data.items.map((item) => (
            <ItemCard key={item.id} item={item} isOwner={mode === 'owner'} refresh={() => void load()} />
          ))}
        </section>
      )}
    </main>
  );
}
