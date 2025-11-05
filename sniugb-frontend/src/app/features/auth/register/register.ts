import { Component } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Se importan los servicios y tipos necesarios
import { ApiService, UserRegisterData } from '../../../services/api';
import { ModalService } from '../../../services/modal.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, NgClass],
  templateUrl: './register.html',
  styleUrls: ['./register.css']
})
export class RegisterComponent {
  // Propiedades para los datos del formulario
  dni: string = '';
  telefono: string = '';
  correo: string = '';
  contrasena: string = '';
  mensaje: string | null = null; // Se renombra para claridad (éxito o error)
  esError: boolean = false; // Para controlar el color del mensaje

  // Objeto para el estado de la validación en tiempo real
  passwordValidation = {
    length: false,
    hasSymbols: false,
    hasNumber: false,
    hasUpper: false
  };

  public showPassword: boolean = false; // Por defecto, la contraseña está oculta

  constructor(
    private apiService: ApiService,
    private modalService: ModalService
  ) {}

  validatePasswordRealtime(): void {
    const pass = this.contrasena;
    this.passwordValidation.length = pass.length >= 8 && pass.length <= 16;
    this.passwordValidation.hasSymbols = /[^a-zA-Z0-9]/.test(pass);
    this.passwordValidation.hasNumber = /\d/.test(pass);
    this.passwordValidation.hasUpper = /[A-Z]/.test(pass);
  }
  
  get isFormInvalid(): boolean {
    return !this.dni || !this.telefono || !this.correo || !this.contrasena;
  }

  registrarse(): void {
    if (this.isFormInvalid) return;
    this.mensaje = null;

    const userData: UserRegisterData = {
      numero_de_dni: this.dni,
      telefono: this.telefono,
      email: this.correo,
      password: this.contrasena
    };

    this.apiService.register(userData).subscribe({
      next: (response) => {
        console.log('Usuario registrado exitosamente:', response);
        
        // --- CORRECCIÓN ---
        // 1. Se establece el mensaje de éxito.
        this.esError = false;
        this.mensaje = '¡Registro exitoso! Ya puede iniciar sesión.';
        
        // 2. Se cierra el modal automáticamente después de 3 segundos.
        setTimeout(() => {
          this.modalService.closeAll();
        }, 3000);
      },
      error: (err) => {
        console.error('Error en el registro:', err.error);
        this.esError = true; // Se marca que es un mensaje de error
        let finalMessage = 'Error inesperado. Intente más tarde.';

        if (err.status === 422 && err.error && Array.isArray(err.error.detail)) {
          const errorInfo = err.error.detail[0];
          const fieldName = errorInfo.loc[1];
          const errorType = errorInfo.type;

          if (fieldName === 'numero_de_dni') {
            finalMessage = 'El DNI debe tener 8 dígitos.';
          } else if (fieldName === 'telefono') {
            finalMessage = 'El teléfono debe tener 9 dígitos.';
          } else if (fieldName === 'email') {
            finalMessage = 'El correo electrónico no es válido.';
          } else {
            finalMessage = 'Revise los datos ingresados.';
          }

        } else if (err.status === 400 && err.error && typeof err.error.detail === 'string') {
          const detail = err.error.detail.toLowerCase();
          if (detail.includes('ya está registrado')) {
            finalMessage = 'El DNI, correo o teléfono ya existe.';
          } else if (detail.includes('contraseña no cumple')) {
            finalMessage = 'La contraseña no cumple los requisitos.';
          } else {
            finalMessage = err.error.detail;
          }
        }
        else if (err.status === 404 && err.error && typeof err.error.detail === 'string') {
          finalMessage = err.error.detail;
        }
        else if (err.status === 500) {
          finalMessage = "Error del servidor. Por favor, intente de nuevo más tarde."
        }
        
        this.mensaje = finalMessage;
      }
    });
  }

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword; // Invierte el valor booleano
  }

}