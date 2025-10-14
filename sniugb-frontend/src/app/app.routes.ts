import { Routes } from '@angular/router';
// --- IMPORTACIÓN DE TODOS LOS GUARDIANES ---
import { authGuard } from './guards/auth-guard';
import { adminGuard } from './guards/admin-guard';
import { publicGuard } from './guards/public-guard';
import { ganaderoGuard } from './guards/ganadero-guard';

export const routes: Routes = [
  // --- Rutas Públicas (Protegidas por publicGuard) ---
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then(m => m.HomeComponent),
    canActivate: [publicGuard] // Impide a usuarios logueados entrar aquí
  },
  {
    path: 'publicaciones',
    loadComponent: () => import('./pages/publicaciones/publicaciones').then(m => m.PublicacionesComponent),
    // Esta ruta puede ser vista por todos, por lo que no necesita guardián.
  },
  
  // --- Rutas Protegidas ---
  {
    path: 'user',
    loadComponent: () => import('./pages/user/user').then(m => m.UserHomeComponent),
    // Se aplican AMBOS guardianes:
    // 1. authGuard: ¿Estás logueado?
    // 2. ganaderoGuard: ¿Eres un ganadero?
    canActivate: [authGuard, ganaderoGuard] 
  },
  {
    path: 'admin',
    loadComponent: () => import('./pages/admin/admin').then(m => m.AdminHomeComponent),
    // Se aplican AMBOS guardianes:
    // 1. authGuard: ¿Estás logueado?
    // 2. adminGuard: ¿Eres un admin?
    canActivate: [authGuard, adminGuard] 
  },

  // Redirección por si el usuario escribe una ruta que no existe
  { path: '**', redirectTo: '', pathMatch: 'full' }
];