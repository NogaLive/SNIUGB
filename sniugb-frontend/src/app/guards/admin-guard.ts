import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Comprueba si el rol del usuario es 'admin'.
  if (authService.obtenerRol() === 'admin') {
    return true; // Si es admin, permite el acceso.
  } else {
    // Si NO es admin, lo redirige a su propio panel de control.
    console.warn('Acceso denegado: Se requiere rol de administrador.');
    router.navigate(['/user']); // Redirige al dashboard de ganadero.
    return false; // Bloquea la navegación a la ruta de admin.
  }
};