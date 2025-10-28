import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { importProvidersFrom, ApplicationConfig, LOCALE_ID } from '@angular/core'; 
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';

// --- IMPORTACIONES AÑADIDAS PARA EL CALENDARIO ---
import { provideCalendar, DateAdapter } from 'angular-calendar';
import { adapterFactory } from 'angular-calendar/date-adapters/date-fns';
// ------------------------------------------------

import { authInterceptor } from './app/services/auth-interceptor'; 
import { routes } from './app/app.routes';
import { AppComponent } from './app/app'; 

registerLocaleData(localeEs);

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])), 
    importProvidersFrom(FormsModule),

    // --- BLOQUE AÑADIDO QUE ARREGLA EL ERROR NG0201 ---
    provideCalendar({
      provide: DateAdapter,
      useFactory: adapterFactory,
    }),
    // --------------------------------------------------

    { provide: LOCALE_ID, useValue: 'es' }
  ]
});