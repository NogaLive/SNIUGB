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
}

/** Tipos de evento (por grupo) */
export interface TipoEventoItem {
  id: number;
  nombre: string;
  grupo: string;
}

/** ======== Sanitarios (masivo) ======== */
export interface EventoSanitarioMasivoCreate {
  fecha_evento_enfermedad: string;
  tipo_evento_enfermedad_id: number;
  fecha_evento_tratamiento?: string | null;
  tipo_evento_tratamiento_id?: number | null;
  nombre_tratamiento?: string | null;
  dosis?: number | null;
  unidad_medida_dosis?: string | null;
  observaciones?: string | null;
  animales_cui: string[];
}

/** ======== Producción (individual) ======== */
export interface EventoProduccionCreate {
  fecha_evento: string;
  /** HTML/TS usan "producto": LECHE | CARNE | CUERO */
  producto: 'LECHE' | 'CARNE' | 'CUERO';
  /** el form usa "valor" (numérico) */
  valor?: number | null;
  unidad_medida?: string | null;
  observaciones?: string | null;
}

/** ======== Control de calidad (masivo) ======== */
export interface ControlCalidadMasivoCreate {
  fecha_evento: string;
  /** el form usa "metodo_id", pero el backend también acepta tipo_evento_calidad_id */
  tipo_evento_calidad_id?: number | null;
  producto: 'LECHE' | 'CARNE' | 'CUERO';
  valor_cantidad?: number | null;
  unidad_medida?: string | null;
  observaciones?: string | null;
  animales_cui: string[];
}

/** ===== NUEVOS MODELOS ===== */
export interface AnimalCreate {
  cui: string;
  nombre?: string | null;
  sexo: 'MACHO' | 'HEMBRA';
  raza: string;
  fecha_nacimiento: string; // YYYY-MM-DD
  predio_codigo: string;
}

export interface Transferencia {
  id: number;
  origen_predio: string;
  destino_predio: string;
  cantidad: number;
  estado: 'pendiente' | 'aprobada' | 'rechazada' | 'cancelada';
  fecha_solicitud: string;
}
export interface TransferCreate {
  origen_predio: string;
  destino_predio: string;
  animal_cuis: string[];
  nota?: string | null;
}

export interface ReporteInfo { key: string; nombre: string; }
export interface ReporteRequest { tipo: string; predio: string; periodo: 'hoy'|'semana'|'mes'; }

export interface InventarioItem {
  id: number;
  predio: string;
  nombre: string;
  cantidad: number;
  unidad: string;
}

export interface Grupo {
  id: number;
  nombre: string;
  predio: string;
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

  // ===== EXISTENTES =====
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

  /** NUEVO: catálogo de razas para "Agregar ganado" */
  getRazas(): Observable<string[]> {
    // Asumiendo que el backend devuelve un array simple de strings.
    return this.http.get<string[]>(this.buildUrl('/utils/razas'));
  }

  getMisPredios(): Observable<PredioResponseSchema[]> {
    return this.http.get<PredioResponseSchema[]>(this.buildUrl('/predios/me'));
  }
  crearPredio(predioData: PredioCreateSchema): Observable<PredioResponseSchema> {
    return this.http.post<PredioResponseSchema>(this.buildUrl('/predios'), predioData);
  }
  getDashboardKpis(predioCodigo: string, periodo: 'hoy' | 'semana' | 'mes') {
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
  getDashboardTabla(
    predioCodigo: string,
    tipo: 'hato' | 'alertas' | 'tareas' | 'produccion' | 'transferencias',
    periodo?: 'hoy' | 'semana' | 'mes'
  ): Observable<any[]> {
    let params = new HttpParams().set('tipo', tipo);
    if (periodo) params = params.set('periodo', periodo);
    return this.http.get<any[]>(this.buildUrl(`/dashboard/${predioCodigo}/tabla`), { params });
  }
  getAnimalByCui(cui: string): Observable<AnimalResponseSchema> {
    return this.http.get<AnimalResponseSchema>(this.buildUrl(`/animales/${encodeURIComponent(cui)}`));
  }

  /** Sanitarios (masivo) */
  crearEventoSanitarioMasivo(body: EventoSanitarioMasivoCreate) {
    return this.http.post(this.buildUrl('/animales/eventos-sanitarios'), body);
  }

  /** Producción (individual) */
  crearEventoProduccion(cui: string, data: EventoProduccionCreate): Observable<any> {
    // El backend acepta "producto" directamente (y también soporta compat de tipo_evento/valor_cantidad)
    return this.http.post<any>(this.buildUrl(`/animales/${encodeURIComponent(cui)}/eventos-produccion`), data);
  }

  /** Control Calidad (masivo) */
  crearControlCalidadMasivo(body: ControlCalidadMasivoCreate | (ControlCalidadMasivoCreate & {metodo_id?: number})) {
    const payload = {
      ...body,
      // tolerancia si el form envía "metodo_id"
      tipo_evento_calidad_id: (body as any).tipo_evento_calidad_id ?? (body as any).metodo_id ?? null
    };
    return this.http.post(this.buildUrl('/animales/control-calidad'), payload);
  }

  /** Tipos de evento por grupo */
  getTiposEventoByGrupo(grupo: string) {
    return this.http.get<TipoEventoItem[]>(this.buildUrl(`/animales/tipos/${grupo}`));
  }

  /** 2) Agregar Ganado */
  crearAnimal(data: AnimalCreate): Observable<AnimalResponseSchema> {
    return this.http.post<AnimalResponseSchema>(this.buildUrl('/animales'), data);
  }
  buscarAnimales(predio: string, q: string = ''): Observable<AnimalResponseSchema[]> {
    let params = new HttpParams().set('predio', predio);
    if (q) params = params.set('q', q);
    return this.http.get<AnimalResponseSchema[]>(this.buildUrl('/animales'), { params });
  }

  /** 3) Transferencias */
  crearTransferencia(body: TransferCreate): Observable<Transferencia> {
    return this.http.post<Transferencia>(this.buildUrl('/transferencias'), body);
  }
  listarTransferencias(scope: 'mine'|'incoming'|'all' = 'mine', estado?: string): Observable<Transferencia[]> {
    let params = new HttpParams().set('scope', scope);
    if (estado) params = params.set('estado', estado);
    return this.http.get<Transferencia[]>(this.buildUrl('/transferencias'), { params });
  }
  aprobarTransferencia(id: number) { return this.http.put(this.buildUrl(`/transferencias/${id}/aprobar`), {}); }
  rechazarTransferencia(id: number) { return this.http.put(this.buildUrl(`/transferencias/${id}/rechazar`), {}); }
  cancelarTransferencia(id: number) { return this.http.put(this.buildUrl(`/transferencias/${id}/cancelar`), {}); }

  /** NUEVO: detalle de transferencia (lista de animales) */
  obtenerDetalleTransferencia(id: number): Observable<AnimalResponseSchema[]> {
    return this.http.get<AnimalResponseSchema[]>(this.buildUrl(`/transferencias/${id}/detalle`));
  }

  /** 4) Reportes */
  getReportesDisponibles(): Observable<ReporteInfo[]> {
    return this.http.get<ReporteInfo[]>(this.buildUrl('/reportes/disponibles'));
  }
  generarReporte(req: { tipo: string; predio: string; periodo: 'hoy'|'semana'|'mes' }): Observable<Blob> {
      return this.http.post(
          this.buildUrl('/reportes/generar'),
          req,
          { responseType: 'blob' }
      );
  }

  /** 5) Inventario */
  getInventario(predio: string): Observable<InventarioItem[]> {
    const params = new HttpParams().set('predio', predio);
    return this.http.get<InventarioItem[]>(this.buildUrl('/inventario'), { params });
  }
  crearInventarioItem(item: Omit<InventarioItem,'id'>): Observable<InventarioItem> {
    return this.http.post<InventarioItem>(this.buildUrl('/inventario'), item);
  }
  actualizarInventarioItem(id: number, item: Partial<InventarioItem>) {
    return this.http.put<InventarioItem>(this.buildUrl(`/inventario/${id}`), item);
  }
  eliminarInventarioItem(id: number) {
    return this.http.delete(this.buildUrl(`/inventario/${id}`));
  }

  /** 9) Grupos */
  listarGrupos(predio: string): Observable<Grupo[]> {
    const params = new HttpParams().set('predio', predio);
    return this.http.get<Grupo[]>(this.buildUrl('/grupos'), { params });
  }
  crearGrupo(nombre: string, predio: string): Observable<Grupo> {
    return this.http.post<Grupo>(this.buildUrl('/grupos'), { nombre, predio });
  }
  getMiembrosGrupo(id: number): Observable<AnimalResponseSchema[]> {
    return this.http.get<AnimalResponseSchema[]>(this.buildUrl(`/grupos/${id}/miembros`));
  }
  addMiembrosGrupo(id: number, cuis: string[]) {
    return this.http.post(this.buildUrl(`/grupos/${id}/miembros`), { cuis });
  }
  removeMiembroGrupo(id: number, cui: string) {
    return this.http.delete(this.buildUrl(`/grupos/${id}/miembros/${encodeURIComponent(cui)}`));
  }

  /** NUEVO: eliminar grupo */
  eliminarGrupo(id: number): Observable<any> {
    return this.http.delete(this.buildUrl(`/grupos/${id}`));
  }
}