import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../services/api';
import { ModalService } from '../../../services/modal.service';
import { AuthStore } from '../../../components/stores/auth.store';

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
    private router: Router,
    private modalService: ModalService,
    private authStore: AuthStore
  ) {}

  openForgotPassword(): void {
    this.modalService.openForgotPassword();
  }

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
    this.resetErrors();

    let validationFailed = false;
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
    if (validationFailed) return;

    this.apiService.login(this.dni, this.contrasena).subscribe({
      next: (response) => {
        // Guardar token + rol en AuthStore (lo mismo que lee el interceptor)
        const role = (response.rol || 'ganadero') as 'admin' | 'ganadero';
        this.authStore.setSession(response.access_token, role);

        this.modalService.closeAll();

        if (role === 'admin') {
          this.router.navigate(['/admin']);
        } else {
          this.router.navigate(['/user']);
        }
      },
      error: (err) => {
        console.error('Error de autenticación:', err);
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
