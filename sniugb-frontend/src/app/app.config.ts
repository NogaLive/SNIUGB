import { ApplicationConfig, LOCALE_ID } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { registerLocaleData } from '@angular/common';
import { es } from 'date-fns/locale';

// --- ESTA ES LA PARTE MÁS IMPORTANTE ---
import { provideCalendar, DateAdapter } from 'angular-calendar';
import { adapterFactory } from 'angular-calendar/date-adapters/date-fns';
// ----------------------------------------

import { routes } from './app.routes';
import { authInterceptor } from './services/auth-interceptor';

registerLocaleData(es); // Esto está bien aquí

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    
    // --- AQUÍ DEBE ESTAR EL PROVIDER ---
    // Si falta este bloque, obtendrás el error NG0201
    provideCalendar({
      provide: DateAdapter,
      useFactory: adapterFactory,
    }),
    
    // Y esto para el idioma
    { provide: LOCALE_ID, useValue: 'es' }
  ]
};