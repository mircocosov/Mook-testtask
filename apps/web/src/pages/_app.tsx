import type { AppProps } from 'next/app';
import { Toaster } from 'sonner';
import '@/styles.scss';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Component {...pageProps} />
      <Toaster richColors position="top-right" />
    </>
  );
}
