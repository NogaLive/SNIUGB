import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth';

// --- AÑADIDO PARA DEPURACIÓN ---
// Este mensaje aparecerá en la consola del navegador si el archivo se carga correctamente.
console.log('DEBUG: El archivo auth-interceptor.ts ha sido cargado por la aplicación.');

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  console.log('Auth Interceptor: La función se está ejecutando...'); 

  const authService = inject(AuthService);
  const authToken = authService.obtenerToken();

  console.log('Auth Interceptor: Token obtenido:', authToken);

  if (authToken) {
    console.log('Auth Interceptor: Añadiendo token al encabezado.');
    const authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${authToken}`
      }
    });
    return next(authReq);
  }

  console.warn('Auth Interceptor: No se encontró token, enviando petición sin autorización.');
  return next(req);
};