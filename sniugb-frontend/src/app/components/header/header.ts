import { Component, OnInit, HostListener, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { Observable } from 'rxjs';

import { ModalService } from '../../services/modal.service';
import { AuthService } from '../../services/auth';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './header.html',
  styleUrls: ['./header.css']
})
export class HeaderComponent implements OnInit {
  isAuthenticated$: Observable<boolean>;
  inicioLink: string = '/';
  
  isMenuOpen: boolean = false;
  nombreUsuario: string = '';

  constructor(
    public modalService: ModalService,
    private authService: AuthService,
    private apiService: ApiService, // Para obtener datos del usuario
    private router: Router,
    private elementRef: ElementRef // Para detectar clics fuera del menú
  ) {
    this.isAuthenticated$ = this.authService.authState$;
  }

  ngOnInit(): void {
    this.isAuthenticated$.subscribe(isAuth => {
      if (isAuth) {
        const rol = this.authService.obtenerRol();
        this.inicioLink = (rol === 'admin') ? '/admin' : '/user';
        this.cargarDatosUsuario(); // Carga el nombre del usuario real
      } else {
        this.inicioLink = '/';
        this.nombreUsuario = ''; // CORRECCIÓN: Limpia el nombre al cerrar sesión
      }
    });
  }

  // CORRECCIÓN: Se activa la llamada a la API para cargar el nombre del usuario.
  cargarDatosUsuario(): void {
    // Asumimos que tienes un endpoint en tu ApiService para obtener el perfil del usuario actual
    this.apiService.getMiPerfil().subscribe({
      next: (usuario) => {
        // Obtiene solo el primer nombre del 'nombre_completo'
        this.nombreUsuario = usuario.nombre_completo.split(' ')[0]; 
      },
      error: (err) => {
        console.error("Error al cargar datos del usuario:", err);
        this.nombreUsuario = 'Usuario'; // Mensaje de fallback en caso de error
      }
    });
  }

  // Abre y cierra el menú
  toggleMenu(): void {
    this.isMenuOpen = !this.isMenuOpen;
  }

  // Cierra el menú si se hace clic fuera de él
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (this.isMenuOpen && !this.elementRef.nativeElement.contains(event.target)) {
      this.isMenuOpen = false;
    }
  }

  // Funcionalidad de cerrar sesión
  logout(): void {
    this.isMenuOpen = false; // Cierra el menú primero
    this.authService.logout();
    this.router.navigate(['/']);
  }
}