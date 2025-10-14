import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const ganaderoGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const userRole = authService.obtenerRol();

  // Comprueba si el rol del usuario es 'ganadero'.
  if (userRole === 'ganadero') {
    return true; // Si es ganadero, permite el acceso.
  } else {
    // Si es admin o cualquier otro rol, lo redirige a su panel.
    router.navigate(['/admin']);
    return false; // Bloquea el acceso a la ruta de ganadero.
  }
};