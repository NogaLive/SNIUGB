import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'sniugb_auth_token'; 
  private readonly ROLE_KEY = 'sniugb_user_role';

  private authState = new BehaviorSubject<boolean>(this.estaAutenticado());
  public authState$ = this.authState.asObservable();

  constructor() { }

  guardarToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
    this.authState.next(true); 
  }

  guardarRol(rol: string): void {
    localStorage.setItem(this.ROLE_KEY, rol);
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.ROLE_KEY);
    this.authState.next(false); 
  }
  
  obtenerToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  obtenerRol(): string | null {
    return localStorage.getItem(this.ROLE_KEY);
  }

  estaAutenticado(): boolean {
    return !!this.obtenerToken(); 
  }

  // --- ¡AQUÍ ESTÁ EL MÉTODO AÑADIDO! ---
  getUserName(): string | null {
    const token = this.obtenerToken();
    if (!token) {
      return null;
    }

    try {
      // Decodifica la parte del payload (el segundo segmento del JWT)
      const payload = JSON.parse(atob(token.split('.')[1]));
      // Asumiendo que guardaste el nombre en el payload como 'nombre_completo'
      return payload.nombre_completo || payload.sub; 
    } catch (e) {
      console.error('Error al decodificar el token:', e);
      return null;
    }
  }
  
} 