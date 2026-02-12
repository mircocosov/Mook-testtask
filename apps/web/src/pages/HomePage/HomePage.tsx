import Link from 'next/link';
import styles from './HomePage.module.scss';

export function HomePage() {
  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1>Wishlist</h1>
        <div>
          <Link href="/auth/login">Войти</Link>
          <Link href="/auth/register">Создать аккаунт</Link>
        </div>
      </header>
      <section className={styles.hero}>
        <p>Подарки без дублей и со складчиной</p>
        <h2>Приватный wishlist для событий</h2>
        <span>Гости резервируют подарки или скидываются на дорогие позиции в realtime.</span>
      </section>
    </main>
  );
}
