import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { Observable } from 'rxjs';

import { HeaderComponent } from './components/header/header';
import { FooterComponent } from './components/footer/footer';

import { ModalService } from './services/modal.service';
import { ModalComponent } from './components/modal/modal';
import { LoginComponent } from './pages/login/login';
import { RegisterComponent } from './pages/register/register';
import { ForgotPasswordComponent } from './pages/forgot-password/forgot-password';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    HeaderComponent,
    FooterComponent,
    ModalComponent,
    LoginComponent,
    RegisterComponent,
    ForgotPasswordComponent
  ],
  
  template: `
    <app-header></app-header>
    <main class="main-container">
      <router-outlet></router-outlet>
    </main>
    <app-footer *ngIf="showFooter"></app-footer>

    <app-modal *ngIf="isLoginOpen$ | async" (close)="modalService.closeAll()" customClass="login-modal">
      <app-login></app-login>
    </app-modal>
    <app-modal *ngIf="isRegisterOpen$ | async" (close)="modalService.closeAll()" customClass="register-modal">
      <app-register></app-register>
    </app-modal>

    <app-modal *ngIf="isForgotPasswordOpen$ | async" (close)="modalService.closeAll()" customClass="forgot-password-modal">
      <app-forgot-password></app-forgot-password>
    </app-modal>
  `
})
export class AppComponent {
  title = 'sniugb-frontend';
  
  public showFooter: boolean = false;

  isLoginOpen$: Observable<boolean>;
  isRegisterOpen$: Observable<boolean>;
  isForgotPasswordOpen$: Observable<boolean>;

  constructor(
    private router: Router,
    public modalService: ModalService
  ) {

    this.isLoginOpen$ = this.modalService.isLoginOpen$;
    this.isRegisterOpen$ = this.modalService.isRegisterOpen$;
    this.isForgotPasswordOpen$ = this.modalService.isForgotPasswordOpen$;
    
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd)
    ).subscribe((event: NavigationEnd) => {
      if (event.url === '/' || event.url === '/inicio') {
        this.showFooter = true;
      } else {
        this.showFooter = false;
      }
    });
  }
}