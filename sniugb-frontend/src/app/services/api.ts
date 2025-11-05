import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
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

@Injectable({ providedIn: 'root' })
export class ApiService {
  private backendUrl = environment.apiBaseUrl.replace(/\/+$/, '');
  constructor(private http: HttpClient) {}

  private buildUrl(path: string): string {
    if (!path) return this.backendUrl;
    const hasProtocol = /^https?:\/\//i.test(path);
    if (hasProtocol) return path;
    const normalized = path.startsWith('/') ? path : '/' + path;
    return this.backendUrl + normalized;
  }

  get<T>(path: string, params?: HttpParams): Observable<T> {
    return this.http.get<T>(this.buildUrl(path), { params });
  }
  post<T>(path: string, body: any, params?: HttpParams): Observable<T> {
    return this.http.post<T>(this.buildUrl(path), body, { params });
  }
  put<T>(path: string, body: any, params?: HttpParams): Observable<T> {
    return this.http.put<T>(this.buildUrl(path), body, { params });
  }
  delete<T>(path: string, params?: HttpParams): Observable<T> {
    return this.http.delete<T>(this.buildUrl(path), { params });
  }

  // Endpoints con '/' final para evitar 307 si el backend usa trailing slash
  getCategorias(): Observable<Categoria[]> {
    return this.http.get<Categoria[]>(this.buildUrl('/categorias/'));
  }

  getArticulos(page: number = 1, categoriaId: number | null = null): Observable<ArticulosResponse> {
    let params = new HttpParams().set('page', page.toString());
    if (categoriaId !== null) params = params.set('categoria_id', categoriaId.toString());
    return this.http.get<ArticulosResponse>(this.buildUrl('/publicaciones/'), { params });
  }

  login(dni: string, contrasena: string): Observable<LoginResponse> {
    const body = new URLSearchParams();
    body.set('username', dni);
    body.set('password', contrasena);
    return this.http.post<LoginResponse>(this.buildUrl('/auth/login'), body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  }

  register(userData: UserRegisterData): Observable<UserResponse> {
    return this.http.post<UserResponse>(this.buildUrl('/auth/register'), userData);
  }
  forgotPassword(data: ForgotPasswordRequest): Observable<ForgotPasswordResponse> {
    return this.http.post<ForgotPasswordResponse>(this.buildUrl('/auth/forgot-password'), data);
  }
  verifyCode(data: VerifyCodeRequest): Observable<any> {
    return this.http.post(this.buildUrl('/auth/verify-code'), data);
  }
  resetPassword(data: ResetPasswordRequest): Observable<any> {
    return this.http.post(this.buildUrl('/auth/reset-password'), data);
  }

  getMiPerfil(): Observable<UserResponse> {
    return this.http.get<UserResponse>(this.buildUrl('/users/me'));
  }
  getArticuloBySlug(slug: string): Observable<Articulo> {
    return this.http.get<Articulo>(this.buildUrl(`/publicaciones/${slug}`));
  }
  getPopularArticles(): Observable<Articulo[]> {
    return this.http.get<Articulo[]>(this.buildUrl('/publicaciones/populares'));
  }
  getRecentArticles(): Observable<Articulo[]> {
    return this.http.get<Articulo[]>(this.buildUrl('/publicaciones/recientes'));
  }
  getDepartamentos(): Observable<SimpleResponse[]> {
    return this.http.get<SimpleResponse[]>(this.buildUrl('/utils/departamentos'));
  }
  getMisPredios(): Observable<PredioResponseSchema[]> {
    return this.http.get<PredioResponseSchema[]>(this.buildUrl('/predios/me'));
  }
  crearPredio(predioData: PredioCreateSchema): Observable<PredioResponseSchema> {
    return this.http.post<PredioResponseSchema>(this.buildUrl('/predios'), predioData);
  }
  getDashboardKpis(predioCodigo: string, periodo: 'hoy' | 'semana' | 'mes'): Observable<KPISchema> {
    const params = new HttpParams().set('periodo', periodo);
    return this.http.get<KPISchema>(this.buildUrl(`/dashboard/${predioCodigo}/kpis`), { params });
  }
  getAnimalesByPredio(predioCodigo: string, estado: 'activo' | 'en_papelera' = 'activo'): Observable<AnimalResponseSchema[]> {
    const params = new HttpParams().set('estado', estado);
    return this.http.get<AnimalResponseSchema[]>(this.buildUrl(`/predios/${predioCodigo}/animales`), { params });
  }
  getRecordatoriosActivos(): Observable<Recordatorio[]> {
    return this.http.get<Recordatorio[]>(this.buildUrl('/calendario/recordatorios-activos'));
  }
  getNotificaciones(): Observable<Notificacion[]> {
    return this.http.get<Notificacion[]>(this.buildUrl('/notificaciones'));
  }
  getEventosDelMes(year: number, month: number): Observable<ApiEvento[]> {
    return this.http.get<ApiEvento[]>(this.buildUrl(`/calendario/eventos/${year}/${month}`));
  }
  toggleRecordatorio(id: number): Observable<any> {
    return this.http.put(this.buildUrl(`/calendario/recordatorios/${id}/toggle-complete`), {});
  }
  marcarNotificacionLeida(id: number): Observable<NotificacionDetailResponseSchema> {
    return this.http.get<NotificacionDetailResponseSchema>(this.buildUrl(`/notificaciones/${id}`));
  }
}