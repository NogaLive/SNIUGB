import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';
import { AuthService } from '../../services/auth';
import { ModalService } from '../../services/modal.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css'] 
})
export class LoginComponent {
  dni: string = '';
  contrasena: string = '';

  dniPlaceholder: string = 'DNI';
  contrasenaPlaceholder: string = 'Contraseña';
  dniError: boolean = false;
  contrasenaError: boolean = false;

  public showPassword: boolean = false;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router,
    private modalService: ModalService
  ) {}

  // Se mantiene tu función para limpiar los errores visuales cuando el usuario escribe.
  resetErrors(): void {
    if (this.dniError || this.contrasenaError) {
      this.dniPlaceholder = 'DNI';
      this.contrasenaPlaceholder = 'Contraseña';
      this.dniError = false;
      this.contrasenaError = false;
    }
  }

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  ingresar(): void {
    // 1. Se resetean los errores visuales de un intento anterior.
    this.resetErrors();

    let validationFailed = false;

    // 2. Se restaura tu validación de campos vacíos. Esto es crucial.
    if (!this.dni) {
      this.dniPlaceholder = 'Ingrese DNI';
      this.dniError = true;
      validationFailed = true;
    }
    if (!this.contrasena) {
      this.contrasenaPlaceholder = 'Ingrese contraseña';
      this.contrasenaError = true;
      validationFailed = true;
    }
    if (validationFailed) {
      return; // Detiene la ejecución si hay campos vacíos.
    }

    // 3. Si todo está bien, se procede con la llamada a la API.
    this.apiService.login(this.dni, this.contrasena).subscribe({
      next: (response) => {
        // Se guarda el token y el rol
        this.authService.guardarToken(response.access_token);
        this.authService.guardarRol(response.rol);
        
        this.modalService.closeAll();

        // --- LÓGICA DE REDIRECCIÓN POR ROL ---
        if (response.rol === 'admin') {
          this.router.navigate(['/admin']); // Redirige al home del admin
        } else {
          this.router.navigate(['/user']); // Redirige al home del ganadero
        }
      },
      error: (err) => {
        console.error('Error de autenticación:', err);
        // Tu lógica de error para credenciales incorrectas se mantiene.
        this.dniPlaceholder = 'Datos incorrectos';
        this.contrasenaPlaceholder = 'Datos incorrectos';
        this.dniError = true;
        this.contrasenaError = true;
        this.dni = '';
        this.contrasena = '';
      }
    });
  }
}