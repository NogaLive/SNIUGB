import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthStore } from '../components/stores/auth.store';

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);
  if (auth.role() !== 'admin') {
    router.navigate(['/user']);
    return false;
  }
  return true;
};
