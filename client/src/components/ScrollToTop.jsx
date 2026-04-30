import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollToTop — resets window scroll position on every route change.
 * Uses 'auto' with requestAnimationFrame to ensure it fires after render.
 */
export default function ScrollToTop() {
  const { pathname, key } = useLocation();

  useEffect(() => {
    requestAnimationFrame(() => {
      window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
    });
  }, [pathname, key]);

  return null;
}
