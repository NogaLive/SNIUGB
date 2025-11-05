import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { adminGuard } from './guards/admin.guard';
import { ganaderoGuard } from './guards/ganadero.guard';
import { publicGuard } from './guards/public.guard';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/home/home').then(m => m.HomeComponent) },

  { path: 'login', loadComponent: () => import('./features/auth/login/login').then(m => m.LoginComponent), canActivate: [publicGuard] },
  { path: 'register', loadComponent: () => import('./features/auth/register/register').then(m => m.RegisterComponent), canActivate: [publicGuard] },
  { path: 'forgot-password', loadComponent: () => import('./features/auth/forgot-password/forgot-password').then(m => m.ForgotPasswordComponent), canActivate: [publicGuard] },

  { path: 'publicaciones', loadComponent: () => import('./features/publicaciones/publicaciones').then(m => m.PublicacionesComponent) },
  { path: 'articulo/:slug', loadComponent: () => import('./features/articulo/articulo').then(m => m.ArticuloComponent) },

  { path: 'user', loadComponent: () => import('./pages/user/user').then(m => m.UserHomeComponent), canActivate: [authGuard, ganaderoGuard] },
  { path: 'admin', loadComponent: () => import('./pages/admin/admin').then(m => m.AdminHomeComponent), canActivate: [authGuard, adminGuard] },

  { path: '**', redirectTo: '', pathMatch: 'full' }
];
