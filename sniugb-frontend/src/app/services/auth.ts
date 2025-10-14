import { Injectable } from '@angular/core';

// --- AÑADIDO: Se importa BehaviorSubject ---
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Asegúrate de que esta cadena sea EXACTAMENTE igual a la de localStorage.
  private readonly TOKEN_KEY = 'sniugb_auth_token'; 
  private readonly ROLE_KEY = 'sniugb_user_role';

  // --- LÓGICA DE ESTADO REACTIVO ---
  // 1. Se crea un BehaviorSubject que guarda el estado de autenticación actual (true/false).
  //    Comienza con el valor que ya exista en localStorage.
  private authState = new BehaviorSubject<boolean>(this.estaAutenticado());

  // 2. Se expone como un observable público. Cualquier componente puede "escuchar" los cambios.
  public authState$ = this.authState.asObservable();

  constructor() { }

  // 3. Se modifican los métodos para que NOTIFIQUEN a los suscriptores de los cambios.
  guardarToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
    this.authState.next(true); // Notifica que el usuario ahora está logueado.
  }

  guardarRol(rol: string): void {
    localStorage.setItem(this.ROLE_KEY, rol);
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.ROLE_KEY);
    this.authState.next(false); // Notifica que el usuario ya NO está logueado.
  }
  
  // --- MÉTODOS EXISTENTES (se mantienen) ---
  obtenerToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  obtenerRol(): string | null {
    return localStorage.getItem(this.ROLE_KEY);
  }

  estaAutenticado(): boolean {
    return !!this.obtenerToken(); 
  }
}