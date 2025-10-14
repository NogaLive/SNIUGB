import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const publicGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Comprueba si el usuario YA está autenticado
  if (authService.estaAutenticado()) {
    // Si está autenticado, no debe estar en las páginas públicas.
    // Lo redirigimos a su panel correspondiente.
    const rol = authService.obtenerRol();
    if (rol === 'admin') {
      router.navigate(['/admin']);
    } else {
      router.navigate(['/user']);
    }
    return false; // Bloquea el acceso a la ruta pública (home, etc.)
  }

  // Si no está autenticado, sí puede ver las páginas públicas.
  return true;
};