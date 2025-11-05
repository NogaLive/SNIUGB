import { Component } from '@angular/core';

@Component({
  standalone: true,
  selector: 'app-admin-home',
  template: `
    <h2 class="text-2xl font-semibold mb-4">Panel del Administrador</h2>
    <p class="opacity-70">Estadísticas globales y gestión de contenido/datos maestros.</p>
  `
})
export class AdminHomeComponent {}
