import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollToTop — resets window scroll position on every route change.
 * Uses 'instant' to avoid annoying slow scroll animation on navigation.
 * Mount once inside <BrowserRouter> (in Layout or App).
 */
export default function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [pathname]);

  return null;
}
