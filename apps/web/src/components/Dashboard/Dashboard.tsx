import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import styles from './Dashboard.module.scss';

type Wishlist = { id: string; title: string; public_id: string };
type Profile = { id: string; email: string; username: string };

export function Dashboard() {
  const [rows, setRows] = useState<Wishlist[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);

  useEffect(() => {
    void api<Wishlist[]>('/wishlists').then(setRows).catch(() => setRows([]));
    void api<Profile>('/auth/me').then(setProfile).catch(() => setProfile(null));
  }, []);

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <div>
          <h1>Мои вишлисты</h1>
          {profile ? <p className={styles.profile}>Вы вошли как @{profile.username}</p> : null}
        </div>
        <Link href="/app/wishlists/new">Создать</Link>
      </div>

      {rows.length === 0 ? (
        <div className={styles.empty}>Пока пусто. Создайте первый wishlist.</div>
      ) : (
        <div className={styles.grid}>
          {rows.map((wishlist) => (
            <Link key={wishlist.id} href={`/app/wishlists/${wishlist.id}`} className={styles.card}>
              <h3>{wishlist.title}</h3>
              <p>/w/{wishlist.public_id}</p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
