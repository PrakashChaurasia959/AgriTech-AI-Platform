import { useEffect } from 'react';

/**
 * Sets the document title to "<pageName> | SmartAgri ML"
 * Resets to the default on unmount.
 */
export function usePageTitle(pageName: string) {
  useEffect(() => {
    const prev = document.title;
    document.title = `${pageName} | SmartAgri ML`;
    return () => { document.title = prev; };
  }, [pageName]);
}
