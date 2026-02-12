import { AuthForm } from '@/components/AuthForm';
import styles from './RegisterPage.module.scss';

export function RegisterPage() {
  return (
    <main className={styles.main}>
      <AuthForm mode="register" />
    </main>
  );
}
