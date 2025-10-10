import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then(m => m.HomeComponent)
  },
  {
    path: 'publicaciones',
    loadComponent: () => import('./pages/publicaciones/publicaciones').then(m => m.PublicacionesComponent)
  },
  {
    path: 'ingresar',
    loadComponent: () => import('./pages/login/login').then(m => m.LoginComponent)
  },
  {
    path: 'registrarse',
    loadComponent: () => import('./pages/register/register').then(m => m.RegisterComponent)
  },
  // Redirección por si el usuario escribe una ruta que no existe
  { path: '**', redirectTo: '', pathMatch: 'full' }
];