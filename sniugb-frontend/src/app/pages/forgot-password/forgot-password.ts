import { Component } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
// CORRECCIÓN: Se importan los nuevos tipos de request
import { ApiService, ForgotPasswordRequest, VerifyCodeRequest, ResetPasswordRequest } from '../../services/api';
import { ModalService } from '../../services/modal.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, FormsModule, NgClass],
  templateUrl: './forgot-password.html',
  styleUrls: ['./forgot-password.css']
})
export class ForgotPasswordComponent {
  currentStep: 'request' | 'verify' | 'reset' = 'request';

  // --- Propiedades para el Paso 1: Request ---
  dni: string = '';
  method: 'email' | 'whatsapp' | null = null;
  mensaje: string | null = null;
  esError: boolean = false;

  // --- Propiedades para el Paso 2: Verify ---
  codigoVerificacion: string = '';

  // --- Propiedades para el Paso 3: Reset ---
  nuevaContrasena: string = '';
  confirmarContrasena: string = '';
  public showPassword: boolean = false;
  public showConfirmPassword: boolean = false;
  passwordValidation = {
    length: false,
    hasSymbols: false,
    hasNumber: false,
    hasUpper: false
  };

  constructor(
    private apiService: ApiService,
    private modalService: ModalService
  ) {}

  resetMessages(): void {
    this.mensaje = null;
    this.esError = false;
  }

  // --- Lógica para el Paso 1: Request ---
  selectMethod(selected: 'email' | 'whatsapp'): void {
    this.method = selected;
    this.resetMessages();
  }
  
  get isRequestFormInvalid(): boolean {
    // CORRECCIÓN: Se elimina la validación [disabled] del botón
    // La validación se hará al hacer clic
    return false; 
  }

  solicitarCodigo(): void {
    this.resetMessages();
    
    // CORRECCIÓN: Validación de campos vacíos al hacer clic
    if (!this.method && !this.dni) {
      this.mensaje = 'Ingrese un DNI y seleccione un método.';
      this.esError = true;
      return;
    }
    if (!this.dni) {
      this.mensaje = 'Por favor, ingresa tu DNI.';
      this.esError = true;
      return;
    }
    if (!this.method) {
      this.mensaje = 'Por favor, seleccione un método.';
      this.esError = true;
      return;
    }

    const requestData: ForgotPasswordRequest = {
      numero_de_dni: this.dni,
      method: this.method!
    };

    this.apiService.forgotPassword(requestData).subscribe({
      next: (response) => {
        this.esError = false;
        this.mensaje = response.message;
        this.currentStep = 'verify'; 
      },
      error: (err) => {
        this.esError = true;
        this.mensaje = err.error?.detail || 'No se pudo procesar la solicitud.';
      }
    });
  }

  // --- Lógica para el Paso 2: Verify ---
  verificarCodigo(): void {
    this.resetMessages();
    
    if (!this.codigoVerificacion) {
      this.mensaje = 'Por favor, ingresa el código.';
      this.esError = true;
      return;
    }

    const verifyData: VerifyCodeRequest = {
      numero_de_dni: this.dni,
      code: this.codigoVerificacion
    };

    this.apiService.verifyCode(verifyData).subscribe({
      next: (response) => {
        this.esError = false;
        this.mensaje = null;
        this.currentStep = 'reset';
      },
      error: (err) => {
        this.esError = true;
        this.mensaje = err.error?.detail || 'No se pudo verificar el código.';
      }
    });
  }

  // --- Lógica para el Paso 3: Reset ---
  validatePasswordRealtime(): void {
    const pass = this.nuevaContrasena;
    this.passwordValidation.length = pass.length >= 8 && pass.length <= 16;
    this.passwordValidation.hasSymbols = /[^a-zA-Z0-9]/.test(pass);
    this.passwordValidation.hasNumber = /\d/.test(pass);
    this.passwordValidation.hasUpper = /[A-Z]/.test(pass);
  }

  // CORRECCIÓN: El getter ahora solo comprueba si los campos están vacíos
  get isResetFormInvalid(): boolean {
    return !this.nuevaContrasena || 
           !this.confirmarContrasena;
  }

  cambiarContrasena(): void {
    this.resetMessages();

    if (this.nuevaContrasena !== this.confirmarContrasena) {
      this.esError = true;
      this.mensaje = 'Las contraseñas no coinciden.';
      return;
    }
    
    // CORRECCIÓN: Se validan los requisitos de la contraseña al hacer clic
    if (!this.passwordValidation.length ||
        !this.passwordValidation.hasSymbols ||
        !this.passwordValidation.hasNumber ||
        !this.passwordValidation.hasUpper) {
      
      this.esError = true;
      this.mensaje = 'La contraseña no cumple los requisitos.';
      return;
    }

    const resetData: ResetPasswordRequest = {
      numero_de_dni: this.dni,
      code: this.codigoVerificacion,
      new_password: this.nuevaContrasena
    };

    this.apiService.resetPassword(resetData).subscribe({
      next: (response) => {
        this.esError = false;
        this.mensaje = 'Contraseña actualizada. Ya puede iniciar sesión.';
        
        setTimeout(() => {
          this.modalService.closeAll();
          this.modalService.openLogin();
        }, 3000);
      },
      error: (err) => {
        this.esError = true;
        this.mensaje = err.error?.detail || 'El código es inválido o ha expirado.';
      }
    });
  }
}