import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthStore } from '../stores/auth.store';

export const ganaderoGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);
  if (auth.role() !== 'ganadero') {
    router.navigate(['/admin']);
    return false;
  }
  return true;
};
