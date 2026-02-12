import { useRouter } from 'next/router';
import { WishlistView } from '@/components/WishlistView';
import styles from './OwnerWishlistPage.module.scss';

export function OwnerWishlistPage() {
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : '';

  if (!id) return <main className={styles.main}>Загрузка...</main>;

  return (
    <main className={styles.main}>
      <WishlistView mode="owner" idOrPublicId={id} />
    </main>
  );
}
