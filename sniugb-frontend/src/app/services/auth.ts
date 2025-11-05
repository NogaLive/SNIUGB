import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEYS = ['access_token', 'sniugb_auth_token'];
  private readonly ROLE_KEYS  = ['role', 'sniugb_user_role'];

  private authState = new BehaviorSubject<boolean>(this.estaAutenticado());
  public authState$ = this.authState.asObservable();

  private writeAll(keys: string[], val: string) {
    keys.forEach(k => localStorage.setItem(k, val));
  }
  private readFirst(keys: string[]) {
    for (const k of keys) {
      const v = localStorage.getItem(k);
      if (v) return v;
    }
    return null;
  }
  private removeAll(keys: string[]) {
    keys.forEach(k => localStorage.removeItem(k));
  }

  guardarToken(token: string): void {
    this.writeAll(this.TOKEN_KEYS, token);
    this.authState.next(true);
  }
  guardarRol(rol: string): void {
    this.writeAll(this.ROLE_KEYS, rol);
  }
  logout(): void {
    this.removeAll(this.TOKEN_KEYS);
    this.removeAll(this.ROLE_KEYS);
    this.authState.next(false);
  }
  obtenerToken(): string | null {
    return this.readFirst(this.TOKEN_KEYS);
  }
  obtenerRol(): string | null {
    return this.readFirst(this.ROLE_KEYS);
  }
  estaAutenticado(): boolean {
    return !!this.obtenerToken();
  }
  getUserName(): string | null {
    const token = this.obtenerToken();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.nombre_completo || payload.sub || null;
    } catch {
      return null;
    }
  }
}
