import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="min-h-screen bg-slate-50 text-slate-900">
      <header class="px-4 py-3 shadow-sm bg-white sticky top-0 z-10">
        <div class="max-w-6xl mx-auto flex items-center justify-between gap-4">
          <a class="font-bold tracking-wide">SNIUGB</a>
          <nav class="text-sm opacity-80">
            <a routerLink="/" class="mr-4 hover:opacity-100">Inicio</a>
            <a routerLink="/publicaciones" class="hover:opacity-100">Publicaciones</a>
          </nav>
        </div>
      </header>
      <main class="max-w-6xl mx-auto px-4 py-6">
        <router-outlet></router-outlet>
      </main>
    </div>
  `
})
export class AppComponent {}
