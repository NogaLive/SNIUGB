import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http'; // Para llamadas a la API
import { FormsModule } from '@angular/forms';
import { importProvidersFrom } from '@angular/core';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(), // Habilita el servicio para hablar con tu backend
    importProvidersFrom(FormsModule) // Habilita el uso de formularios
  ]
};