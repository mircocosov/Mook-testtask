import styles from './ItemCard.module.scss';
import { api } from '@/lib/api';

export type PublicItem = {
  id: string;
  title: string;
  url?: string;
  image_url?: string;
  price_amount?: number;
  currency: string;
  status: string;
  reserved: boolean;
  contributed_amount: number;
};

type Props = {
  item: PublicItem;
  isOwner: boolean;
  refresh: () => void;
};

export function ItemCard({ item, isOwner, refresh }: Props) {
  const progress = item.price_amount
    ? Math.min(100, Math.round((item.contributed_amount / item.price_amount) * 100))
    : 0;

  async function reserve() {
    await api(`/public/items/${item.id}/reserve`, { method: 'POST' });
    refresh();
  }

  async function unreserve() {
    await api(`/public/items/${item.id}/unreserve`, { method: 'POST' });
    refresh();
  }

  async function contribute() {
    const value = window.prompt('Введите сумму в центах');
    const amount = Number(value);
    if (!amount) return;
    await api(`/public/items/${item.id}/contribute`, {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
    refresh();
  }

  return (
    <article className={styles.card}>
      {item.image_url ? <img src={item.image_url} alt={item.title} /> : <div className={styles.placeholder} />}
      <div className={styles.content}>
        <div className={styles.titleRow}>
          <h3>{item.title}</h3>
          {item.reserved ? <span>Reserved</span> : null}
        </div>
        {item.price_amount ? (
          <>
            <p className={styles.price}>Цель: {(item.price_amount / 100).toFixed(2)} {item.currency}</p>
            <div className={styles.progress}><div style={{ width: `${progress}%` }} /></div>
            <p className={styles.price}>Собрано {(item.contributed_amount / 100).toFixed(2)}</p>
          </>
        ) : null}
        {item.url ? <a href={item.url} target="_blank" rel="noreferrer">Ссылка на товар</a> : null}
        {!isOwner && item.status === 'active' ? (
          <div className={styles.actions}>
            {item.reserved ? <button onClick={unreserve}>Отменить резерв</button> : <button onClick={reserve}>Reserve</button>}
            <button onClick={contribute}>Contribute</button>
          </div>
        ) : null}
      </div>
    </article>
  );
}
