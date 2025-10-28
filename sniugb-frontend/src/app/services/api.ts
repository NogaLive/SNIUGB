import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Articulo } from '../models/articulo.model';
import { Categoria } from '../models/categoria.model';

// --- INTERFACES (Tus modelos de datos) ---
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
export interface ForgotPasswordRequest {
  numero_de_dni: string;
  method: 'email' | 'whatsapp';
}
export interface ForgotPasswordResponse {
  message: string;
}
export interface VerifyCodeRequest {
  numero_de_dni: string;
  code: string;
}
export interface ResetPasswordRequest {
  numero_de_dni: string;
  code: string;
  new_password: string;
}
export interface UserResponse {
  numero_de_dni: string;
  nombre_completo: string;
  email: string;
  telefono: string;
  rol: string;
}

export interface SimpleResponse {
  nombre: string;
}

export interface PredioResponseSchema {
  codigo_predio: string;
  nombre_predio: string;
  departamento: string;
  ubicacion: string;
  propietario_dni: string;
}

export interface PredioCreateSchema {
  nombre_predio: string;
  departamento: string;
  ubicacion: string;
}

export interface AnimalResponseSchema {
  cui: string;
  nombre: string;
  sexo: string;
  peso: string;
  estado: string;
  condicion_salud: string;
  raza: { nombre: string }; 
  fecha_nacimiento: string;
}

export interface KPISchema {
  total_hato: number;
  alertas_salud: number;
  tareas_para_hoy: number;
  produccion_reciente_carne: number;
  produccion_reciente_leche: number;
  solicitudes_transferencia: number;
}

// Coincide con notificacion_models.py
export interface Notificacion { 
  id: number;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
  link: string | null;
}

export interface NotificacionDetailResponseSchema extends Notificacion {
  detalles_transferencia: any | null; 
}

export interface Recordatorio {
  id: number;
  titulo: string;
  es_completado: boolean;
  fecha_evento: string; 
}

export interface ApiEvento {
  id: number;
  fecha_evento: string;
  titulo: string;
  tipo: string; 
  descripcion?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) { }

  // --- MÉTODOS EXISTENTES ---
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
  forgotPassword(data: ForgotPasswordRequest): Observable<ForgotPasswordResponse> {
    return this.http.post<ForgotPasswordResponse>(`${this.backendUrl}/auth/forgot-password`, data);
  }
  verifyCode(data: VerifyCodeRequest): Observable<any> {
    return this.http.post(`${this.backendUrl}/auth/verify-code`, data);
  }
  resetPassword(data: ResetPasswordRequest): Observable<any> {
    return this.http.post(`${this.backendUrl}/auth/reset-password`, data);
  }
  getMiPerfil(): Observable<UserResponse> {
    return this.http.get<UserResponse>(`${this.backendUrl}/users/me`);
  }
  getArticuloBySlug(slug: string): Observable<Articulo> {
    return this.http.get<Articulo>(`${this.backendUrl}/publicaciones/${slug}`);
  }
  getPopularArticles(): Observable<Articulo[]> {
    return this.http.get<Articulo[]>(`${this.backendUrl}/publicaciones/populares`);
  }
  getRecentArticles(): Observable<Articulo[]> {
    return this.http.get<Articulo[]>(`${this.backendUrl}/publicaciones/recientes`);
  }

  // --- MÉTODOS NUEVOS Y ACTUALIZADOS ---

  getDepartamentos(): Observable<SimpleResponse[]> {
    return this.http.get<SimpleResponse[]>(`${this.backendUrl}/utils/departamentos`);
  }

  getMisPredios(): Observable<PredioResponseSchema[]> {
    return this.http.get<PredioResponseSchema[]>(`${this.backendUrl}/predios/me`);
  }
  
  crearPredio(predioData: PredioCreateSchema): Observable<PredioResponseSchema> {
    return this.http.post<PredioResponseSchema>(`${this.backendUrl}/predios/`, predioData);
  }

  getDashboardKpis(predioCodigo: string, periodo: 'hoy' | 'semana' | 'mes'): Observable<KPISchema> {
    let params = new HttpParams().set('periodo', periodo);
    return this.http.get<KPISchema>(`${this.backendUrl}/dashboard/${predioCodigo}/kpis`, { params });
  }

  getAnimalesByPredio(predioCodigo: string, estado: 'activo' | 'en_papelera' = 'activo'): Observable<AnimalResponseSchema[]> {
    let params = new HttpParams().set('estado', estado);
    return this.http.get<AnimalResponseSchema[]>(`${this.backendUrl}/predios/${predioCodigo}/animales`, { params });
  }
  
  getRecordatoriosActivos(): Observable<Recordatorio[]> {
    return this.http.get<Recordatorio[]>(`${this.backendUrl}/calendario/recordatorios-activos`);
  }

  // ARREGLADO (Error 422): La ruta es "/" (la base del router), no "/me"
  // Esto coincide con @notificaciones_router.get("/")
  getNotificaciones(): Observable<Notificacion[]> {
    return this.http.get<Notificacion[]>(`${this.backendUrl}/notificaciones/`); 
  }

  getEventosDelMes(year: number, month: number): Observable<ApiEvento[]> {
    return this.http.get<ApiEvento[]>(`${this.backendUrl}/calendario/eventos/${year}/${month}`);
  }

  toggleRecordatorio(id: number): Observable<any> {
    return this.http.put(`${this.backendUrl}/calendario/recordatorios/${id}/toggle-complete`, {});
  }
  
  // ARREGLADO: Tu backend (notificaciones.py) marca como leída al hacer GET a "/{notificacion_id}"
  // Esto coincide con @notificaciones_router.get("/{notificacion_id}")
  marcarNotificacionLeida(id: number): Observable<NotificacionDetailResponseSchema> {
    return this.http.get<NotificacionDetailResponseSchema>(`${this.backendUrl}/notificaciones/${id}`);
  }
}