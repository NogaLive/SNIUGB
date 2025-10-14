import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Articulo } from '../models/articulo.model';
import { Categoria } from '../models/categoria.model';

export interface ArticulosResponse {
  articulos: Articulo[];
  total: number;
  page: number;
  pages: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  rol: string; 
}

export interface UserRegisterData {
  numero_de_dni: string;
  telefono: string;
  email: string;
  password: string;
}

export interface UserResponse {
  numero_de_dni: string;
  nombre_completo: string;
  email: string;
  telefono: string;
  rol: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) { }

  getCategorias(): Observable<Categoria[]> {
    return this.http.get<Categoria[]>(`${this.backendUrl}/categorias/`);
  }

  getArticulos(page: number = 1, categoriaId: number | null = null): Observable<ArticulosResponse> {
    let params = new HttpParams().set('page', page.toString());

    if (categoriaId !== null) {
      params = params.set('categoria_id', categoriaId.toString());
    }

    return this.http.get<ArticulosResponse>(`${this.backendUrl}/publicaciones/`, { params });
  }

  login(dni: string, contrasena: string): Observable<LoginResponse> {
    const body = new URLSearchParams();
    body.set('username', dni);
    body.set('password', contrasena);
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
    return this.http.post<LoginResponse>(`${this.backendUrl}/auth/login`, body.toString(), { headers });
  }

  register(userData: UserRegisterData): Observable<UserResponse> {
    return this.http.post<UserResponse>(`${this.backendUrl}/auth/register`, userData);
  }

  getMiPerfil(): Observable<UserResponse> {
    return this.http.get<UserResponse>(`${this.backendUrl}/users/me`);
  }
}