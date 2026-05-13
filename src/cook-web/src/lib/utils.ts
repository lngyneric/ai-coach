import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const redirectToHomeUrlIfRootPath = (homeUrl?: string): boolean => {
  if (typeof window === 'undefined' || !homeUrl) {
    return false;
  }

  const pathname = window.location.pathname || '/';
  const normalizedPath = pathname === '/' ? '/' : pathname.replace(/\/+$/, '');
  const shouldRedirect = normalizedPath === '/' || normalizedPath === '/c';

  // Avoid redirect loop: skip if current path already matches homeUrl
  if (shouldRedirect && normalizedPath === homeUrl) {
    return false;
  }

  if (shouldRedirect) {
    window.location.replace(homeUrl);
    return true;
  }

  return false;
};