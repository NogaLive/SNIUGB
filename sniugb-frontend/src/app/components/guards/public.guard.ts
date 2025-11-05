import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthStore } from '../stores/auth.store';

export const publicGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);
  if (auth.isLoggedIn()) {
    router.navigate([auth.role() === 'admin' ? '/admin' : '/user']);
    return false;
  }
  return true;
};
