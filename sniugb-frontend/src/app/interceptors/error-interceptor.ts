import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';

export const ErrorInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe();
  // Puedes añadir catchError aquí para mostrar toasts/notificaciones globales.
};
