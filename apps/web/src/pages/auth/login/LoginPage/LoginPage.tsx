import { AuthForm } from '@/components/AuthForm';
import styles from './LoginPage.module.scss';

export function LoginPage() {
  return (
    <main className={styles.main}>
      <AuthForm mode="login" />
    </main>
  );
}
