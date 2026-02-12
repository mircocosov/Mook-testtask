import { useRouter } from 'next/router';
import { WishlistView } from '@/components/WishlistView';
import styles from './PublicWishlistPage.module.scss';

export function PublicWishlistPage() {
  const router = useRouter();
  const publicId = typeof router.query.public_id === 'string' ? router.query.public_id : '';

  if (!publicId) return <main className={styles.main}>Загрузка...</main>;

  return (
    <main className={styles.main}>
      <WishlistView mode="public" idOrPublicId={publicId} />
    </main>
  );
}
