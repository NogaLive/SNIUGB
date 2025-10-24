import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { importProvidersFrom } from '@angular/core';

import { ApplicationConfig, LOCALE_ID } from '@angular/core'; 
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';

import { authInterceptor } from './app/services/auth-interceptor'; 
import { routes } from './app/app.routes';
import { AppComponent } from './app/app'; 

registerLocaleData(localeEs);

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])), 
    importProvidersFrom(FormsModule),

    { provide: LOCALE_ID, useValue: 'es' }
  ]
});