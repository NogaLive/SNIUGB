import { Routes } from '@angular/router';

export const ADMIN_ROUTES: Routes = [
  { path: '', pathMatch: 'full', loadComponent: () => import('./admin-home.component').then(m => m.AdminHomeComponent) },
];
