import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { importProvidersFrom } from '@angular/core';

import { routes } from './app/app.routes';
import { AppComponent } from './app/app'; // Apunta al archivo app.ts

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(), // Habilita las llamadas a tu API
    importProvidersFrom(FormsModule) // Habilita el uso de formularios
  ]
});