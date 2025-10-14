import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Comprueba si el usuario está autenticado
  if (authService.estaAutenticado()) {
    return true; // Si está autenticado, permite el acceso.
  } else {
    // Si NO está autenticado, lo redirige a la página de inicio.
    console.error('Acceso denegado: Se requiere autenticación.');
    router.navigate(['/']); 
    return false; // Bloquea la navegación.
  }
};