import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ModalService {
  // BehaviorSubjects para mantener el estado de visibilidad de cada modal
  private isLoginOpen = new BehaviorSubject<boolean>(false);
  private isRegisterOpen = new BehaviorSubject<boolean>(false);
  private isForgotPasswordOpen = new BehaviorSubject<boolean>(false);

  // Observables públicos para que los componentes se suscriban a los cambios
  isLoginOpen$ = this.isLoginOpen.asObservable();
  isRegisterOpen$ = this.isRegisterOpen.asObservable();
  isForgotPasswordOpen$ = this.isForgotPasswordOpen.asObservable();

  constructor() { }

  // Métodos para abrir los modales
  openLogin(): void {
    this.isRegisterOpen.next(false);
    this.isForgotPasswordOpen.next(false);
    this.isLoginOpen.next(true);
  }

  openRegister(): void {
    this.isLoginOpen.next(false);
    this.isForgotPasswordOpen.next(false);
    this.isRegisterOpen.next(true);
  }

  openForgotPassword(): void {
    this.isLoginOpen.next(false);
    this.isRegisterOpen.next(false);
    this.isForgotPasswordOpen.next(true);
  }

  // Método para cerrar todos los modales
  closeAll(): void {
    this.isLoginOpen.next(false);
    this.isRegisterOpen.next(false);
    this.isForgotPasswordOpen.next(false);
  }
}