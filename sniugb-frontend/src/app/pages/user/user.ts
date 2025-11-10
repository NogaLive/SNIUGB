import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, TitleCasePipe } from '@angular/common';
import { Router, RouterLink, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { catchError, of } from 'rxjs';

import { FullCalendarModule } from '@fullcalendar/angular';
import { CalendarOptions, EventInput } from '@fullcalendar/core';
import esLocale from '@fullcalendar/core/locales/es';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';

import { PredioModalComponent } from '../../components/predio-modal/predio-modal';
import { UiModalComponent } from '../../components/ui-modal/ui-modal';

import {
  ApiService,
  KPISchema,
  Recordatorio,
  ApiEvento,
  PredioResponseSchema,
  Notificacion,
  EventoSanitarioCreate,
  EventoProduccionCreate,
  AnimalResponseSchema,
} from '../../services/api';
import { AuthService } from '../../services/auth';

type CentroActividadTab = 'notificaciones' | 'recordatorios';
type Periodo = 'hoy' | 'semana' | 'mes';
type ModalKey =
  | 'buscar'
  | 'agregar'
  | 'transferencias'
  | 'reportes'
  | 'inventario'
  | 'sanitario'
  | 'produccion'   // nuevo: Eventos de producción (una por animal)
  | 'calidad'      // nuevo: Control de Calidad (multi)
  | 'grupos'
  | null;

@Component({
  selector: 'app-user',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterModule,
    FormsModule,
    PredioModalComponent,
    UiModalComponent,
    DatePipe,
    TitleCasePipe,
    FullCalendarModule
  ],
  templateUrl: './user.html',
  styleUrls: ['./user.css'],
})
export class UserHomeComponent implements OnInit {
  public locale: string = 'es';
  isLoading = true;
  mostrarModalCrearPredio = false;
  listaDePredios: PredioResponseSchema[] = [];
  predioActivoCodigo: string | null = null;

  kpis: KPISchema | null = null;

  periodoTareas: Periodo = 'hoy';
  periodoTareasLabel = 'Hoy';
  periodoProduccion: Periodo = 'hoy';
  periodoProduccionLabel = 'Hoy';
  periodoKpiProduccion: Periodo = 'hoy';

  tablaModo: 'hato' | 'alertas' | 'tareas' | 'produccion' | 'transferencias' = 'hato';
  tablaTitulo = 'Mi Hato (Últimos Registros)';
  tablaCols: { key: string; label: string }[] = [];
  tablaRows: any[] = [];

  activeTab: CentroActividadTab = 'notificaciones';
  notificaciones: Notificacion[] = [];
  recordatoriosActivos: Recordatorio[] = [];

  calendarViewDate: Date = new Date();
  calendarOptions!: CalendarOptions;
  fcEvents: EventInput[] = [];
  selectedDate: Date | null = null;

  /* ===== MODALES ===== */
  activeModal: ModalKey = null;
  submitting = false; // Loader “Guardando…” compartido

  // cache animales para el buscador
  cachedAnimales: AnimalResponseSchema[] = [];
  animalQuery = '';
  animalSuggestions: AnimalResponseSchema[] = [];
  // selección de animales (usa sólo cui + nombre para chips)
  selectedAnimals: { cui: string; nombre: string }[] = [];

  /* Formularios */
  formBuscar = { cui: '' };

  formSanitario: EventoSanitarioCreate & { /* masivo */ } = {
    fecha_evento: new Date().toISOString().slice(0,16),
    tipo_evento: 'Vacunación',
    producto_nombre: '',
    dosis: '',
    observaciones: ''
  } as any;

  // Producción (una por animal; selecciona UN animal en chips)
  formProduccion: EventoProduccionCreate & { producto: 'LECHE'|'CARNE'|'CUERO' } = {
    fecha_evento: new Date().toISOString().slice(0,16),
    tipo_evento: 'Pesaje', // seguirá usándose para pesaje si lo necesitas interno
    valor: '',
    observaciones: '',
    producto: 'LECHE',
  } as any;

  // Control de Calidad (multi-animales)
  formCalidad = {
    fecha_evento: new Date().toISOString().slice(0,16),
    producto: 'LECHE' as 'LECHE'|'CARNE'|'CUERO',
    metodo_id: null as number | null, // vendrá de TipoEvento(grupo=CONTROL_CALIDAD) cuando expongas endpoint
    valor: '',
    unidad_medida: '',
    observaciones: ''
  };

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initCalendarOptions();
    this.cargarDatosIniciales();
  }

  /* ---------- FullCalendar ---------- */
  private initCalendarOptions(): void {
    this.calendarOptions = {
      plugins: [dayGridPlugin, interactionPlugin],
      initialView: 'dayGridMonth',
      locales: [esLocale],
      locale: 'es',
      firstDay: 1,
      fixedWeekCount: false,
      showNonCurrentDates: true,
      headerToolbar: false,
      initialDate: this.calendarViewDate,
      events: this.fcEvents,
      dateClick: (info) => this.onDateClick(info.date),
      datesSet: (arg) => {
        const center = new Date(arg.start); center.setDate(center.getDate() + 15);
        this.calendarViewDate = center; this.loadEventosDelMes();
      },
      dayCellClassNames: (arg) => {
        const classes: string[] = [];
        if (this.isSelected(arg.date)) classes.push('is-selected');
        if (this.isWeekend(arg.date)) classes.push('is-weekend');
        if (this.hasEventsDate(arg.date)) classes.push('has-events');
        if (this.hasReminderDate(arg.date)) classes.push('has-reminder');
        return classes;
      },
    };
  }

  /* ---------- Cargas ---------- */
  cargarDatosIniciales(): void {
    this.isLoading = true;
    this.apiService.getMisPredios().pipe(
      catchError((err: any) => { console.error('Error fatal al cargar predios:', err); this.isLoading = false; return of([]); })
    ).subscribe((predios: PredioResponseSchema[]) => {
      if (predios.length === 0) {
        this.mostrarModalCrearPredio = true; this.isLoading = false;
      } else {
        this.listaDePredios = predios;
        this.predioActivoCodigo = predios[0].codigo_predio;
        this.cargarDatosDashboard(this.predioActivoCodigo);
        this.cargarDatosSidebar();
        this.tablaModo = 'hato'; this.tablaTitulo = 'Mi Hato (Últimos Registros)'; this.cargarTabla();
        this.precargarAnimalesDelPredio(); // para el buscador con chips
      }
    });
  }

  private precargarAnimalesDelPredio(): void {
    if (!this.predioActivoCodigo) return;
    this.apiService.getAnimalesByPredio(this.predioActivoCodigo, 'activo')
      .pipe(catchError(() => of([])))
      .subscribe(list => { this.cachedAnimales = list || []; this.filtrarSugerencias(''); });
  }

  cargarDatosDashboard(codigoPredio: string): void {
    if (!codigoPredio) return;
    this.isLoading = true; this.kpis = null;
    this.apiService.getDashboardKpis(codigoPredio, this.periodoKpiProduccion).pipe(
      catchError((err: any) => { console.error('Error al cargar KPIs:', err); this.isLoading = false; return of(null); })
    ).subscribe((data: KPISchema | null) => { this.kpis = data; if (data) this.isLoading = false; });
  }

  cargarDatosSidebar(): void {
    this.apiService.getRecordatoriosActivos().pipe(catchError((_: any) => of([]))).subscribe(d => this.recordatoriosActivos = d);
    this.apiService.getNotificaciones().pipe(catchError((_: any) => of([]))).subscribe(d => this.notificaciones = d);
    this.loadEventosDelMes();
  }

  loadEventosDelMes(): void {
    const year = this.calendarViewDate.getFullYear(), month = this.calendarViewDate.getMonth() + 1;
    this.apiService.getEventosDelMes(year, month).pipe(
      catchError((err: any) => { console.error('Error al cargar eventos del calendario:', err); return of([]); })
    ).subscribe((eventos: ApiEvento[]) => {
      this.fcEvents = eventos.map(e => ({ start: new Date(e.fecha_evento), title: e.titulo, extendedProps: { tipo: e.tipo } }));
      this.calendarOptions = { ...this.calendarOptions, events: this.fcEvents };
    });
  }

  /* ---------- Predio ---------- */
  onPredioCreado(_: PredioResponseSchema): void { this.mostrarModalCrearPredio = false; this.cargarDatosIniciales(); }
  onPredioChange(): void {
    if (!this.predioActivoCodigo) return;
    if (this.predioActivoCodigo === 'CREAR_NUEVO') {
      this.predioActivoCodigo = this.listaDePredios.length > 0 ? this.listaDePredios[0].codigo_predio : null;
      this.mostrarModalCrearPredio = true;
    } else { this.cargarDatosDashboard(this.predioActivoCodigo); this.cargarTabla(); this.precargarAnimalesDelPredio(); }
  }

  /* ---------- KPIs ---------- */
  onKpiHatoClick(): void { this.tablaModo = 'hato'; this.tablaTitulo = 'Mi Hato (Registro total)'; this.cargarTabla(); }
  onKpiAlertasClick(): void { this.tablaModo = 'alertas'; this.tablaTitulo = 'Alertas de salud (Mes actual)'; this.cargarTabla(); }
  onKpiTareasClick(): void {
    if (this.periodoTareas === 'hoy') { this.periodoTareas = 'semana'; this.periodoTareasLabel = 'Semana'; }
    else if (this.periodoTareas === 'semana') { this.periodoTareas = 'mes'; this.periodoTareasLabel = 'Mes'; }
    else { this.periodoTareas = 'hoy'; this.periodoTareasLabel = 'Hoy'; }
    this.tablaModo = 'tareas'; this.tablaTitulo = `Tareas Pendientes (${this.periodoTareasLabel})`; this.cargarTabla();
  }
  onKpiProduccionKpiClick(): void {
    if (this.periodoProduccion === 'hoy') { this.periodoProduccion = 'semana'; this.periodoProduccionLabel = 'Semana'; }
    else if (this.periodoProduccion === 'semana') { this.periodoProduccion = 'mes'; this.periodoProduccionLabel = 'Mes'; }
    else { this.periodoProduccion = 'hoy'; this.periodoProduccionLabel = 'Hoy'; }
    this.periodoKpiProduccion = this.periodoProduccion;
    if (this.predioActivoCodigo) this.apiService.getDashboardKpis(this.predioActivoCodigo, this.periodoKpiProduccion)
      .pipe(catchError(() => of(null))).subscribe(d => this.kpis = d);
    this.tablaModo = 'produccion'; this.tablaTitulo = `Producción (${this.periodoProduccionLabel})`; this.cargarTabla();
  }
  onKpiTransferenciasClick(): void { this.tablaModo = 'transferencias'; this.tablaTitulo = 'Transferencias Pendientes'; this.cargarTabla(); }

  /* ---------- Tabla inferior ---------- */
  private cargarTabla(): void {
    if (!this.predioActivoCodigo) return;

    if (this.tablaModo === 'hato' || this.tablaModo === 'alertas') {
      this.tablaCols = [
        { key: 'cui', label: 'CUI' },
        { key: 'nombre', label: 'Nombre' },
        { key: 'raza', label: 'Raza' },
        { key: 'sexo', label: 'Sexo' },
        { key: 'fecha_nacimiento', label: 'Nacimiento' },
        { key: 'condicion_salud', label: 'Salud' },
        { key: 'estado', label: 'Estado' },
      ];
    } else if (this.tablaModo === 'tareas') {
      this.tablaCols = [
        { key: 'fecha_evento', label: 'Fecha' },
        { key: 'titulo', label: 'Título' },
        { key: 'tipo', label: 'Tipo' },
      ];
    } else if (this.tablaModo === 'produccion') {
      this.tablaCols = [
        { key: 'fecha_evento', label: 'Fecha' },
        { key: 'animal_cui', label: 'CUI' },
        { key: 'tipo_evento', label: 'Evento' },
        { key: 'valor', label: 'Valor' },
        { key: 'observaciones', label: 'Obs.' },
      ];
    } else if (this.tablaModo === 'transferencias') {
      this.tablaCols = [
        { key: 'id', label: 'ID' },
        { key: 'solicitante', label: 'Solicitante' },
        { key: 'cantidad', label: '# Animales' },
        { key: 'fecha_solicitud', label: 'Fecha' },
        { key: 'estado', label: 'Estado' },
      ];
    }

    const periodo: Periodo | undefined =
      this.tablaModo === 'tareas' ? this.periodoTareas :
      this.tablaModo === 'produccion' ? this.periodoProduccion :
      undefined;

    this.apiService.getDashboardTabla(this.predioActivoCodigo, this.tablaModo, periodo)
      .pipe(catchError(() => of([])))
      .subscribe((rows: any[]) => this.tablaRows = rows || []);
  }

  /* ---------- Sidebar ---------- */
  seleccionarTab(tab: CentroActividadTab): void { this.activeTab = tab; }
  marcarNotificacionLeida(notif: Notificacion): void {
    if (notif.leida && !notif.link) return;
    this.apiService.marcarNotificacionLeida(notif.id).subscribe({
      next: (detalle) => { notif.leida = true; if (detalle.link) this.router.navigate([detalle.link]); },
      error: (err: any) => console.error('Error al marcar notificación como leída:', err)
    });
  }
  toggleRecordatorio(recordatorio: Recordatorio): void {
    this.apiService.toggleRecordatorio(recordatorio.id).subscribe({
      next: () => this.cargarDatosSidebar(),
      error: (err: any) => console.error('Error al actualizar recordatorio:', err)
    });
  }

  /* ---------- Calendario ---------- */
  private sameDay(a: Date, b: Date): boolean { return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); }
  onDateClick(date: Date): void { this.selectedDate = date; this.calendarOptions = { ...this.calendarOptions }; }
  isSelected(d: Date): boolean { return !!this.selectedDate && this.sameDay(this.selectedDate, d); }
  isWeekend(d: Date): boolean { const w = d.getDay(); return w === 0 || w === 6; }
  private hasEventsDate(date: Date): boolean { return this.fcEvents?.some(e => e.start && this.sameDay(new Date(e.start as any), date)); }
  private hasReminderDate(date: Date): boolean {
    return this.fcEvents?.some(e => { const isSame = e.start && this.sameDay(new Date(e.start as any), date); const tipo = (e.extendedProps as any)?.tipo; return isSame && tipo === 'RECORDATORIO'; }) || false;
  }
  cambiarMes(offset: number): void {
    const d = new Date(this.calendarViewDate); d.setMonth(d.getMonth() + offset); this.calendarViewDate = d;
    this.calendarOptions = { ...this.calendarOptions, initialDate: this.calendarViewDate }; this.loadEventosDelMes();
  }

  /* ======= MODALES ======= */
  openModal(key: Exclude<ModalKey, null>) {
    this.activeModal = key;
    this.submitting = false;
    // limpiar selección de animales cada vez
    this.selectedAnimals = [];
    this.animalQuery = '';
    this.filtrarSugerencias('');
  }
  closeModal() { this.activeModal = null; this.submitting = false; }

  // Panel de control
  goBuscarRegistro() { this.openModal('buscar'); }
  goAgregarGanado()   { this.openModal('agregar'); }
  goTransferencias()  { this.openModal('transferencias'); }
  goReportes()        { this.openModal('reportes'); }
  goInventario()      { this.openModal('inventario'); }

  // Panel de gestión (nuevo set)
  goGestionSanitarioMasivo() { this.openModal('sanitario'); }
  goGestionEventosProduccion() { this.openModal('produccion'); }
  goGestionControlCalidad()   { this.openModal('calidad'); }
  goGestionGrupos()           { this.openModal('grupos'); }

  /* ====== Buscador con chips (animales) ====== */
  filtrarSugerencias(q: string) {
    const query = (q || '').trim().toLowerCase();
    this.animalSuggestions = (this.cachedAnimales || [])
      .filter(a =>
        !this.selectedAnimals.find(s => s.cui === a.cui) &&
        (query === '' ||
         a.cui.toLowerCase().includes(query) ||
         (a.nombre || '').toLowerCase().includes(query))
      )
      .slice(0, 10);
  }
  onAnimalQueryChange() { this.filtrarSugerencias(this.animalQuery); }
  addAnimal(a: AnimalResponseSchema) {
    this.selectedAnimals.push({ cui: a.cui, nombre: a.nombre || a.cui });
    this.animalQuery = ''; this.filtrarSugerencias('');
  }
  removeAnimal(idx: number) { this.selectedAnimals.splice(idx, 1); this.filtrarSugerencias(this.animalQuery); }

  /* ===== Submits ===== */

  submitBuscar(): void {
    const cui = (this.formBuscar.cui || '').trim();
    if (!cui) return;
    this.submitting = true;
    this.apiService.getAnimalByCui(cui).pipe(catchError(() => of(null))).subscribe((a) => {
      this.submitting = false;
      if (a?.cui) {
        this.closeModal();
        this.router.navigate(['/user/animal', a.cui]);
      } else {
        alert('No se encontró el CUI ingresado.');
      }
    });
  }

  // Evento Sanitario (masivo: usa selectedAnimals)
  submitSanitario(): void {
    if (this.selectedAnimals.length === 0) { alert('Selecciona al menos un animal.'); return; }
    const base = { ...this.formSanitario };
    if ((base.fecha_evento as string).length <= 16) base.fecha_evento = (base.fecha_evento as string) + ':00Z';

    this.submitting = true;
    Promise.all(
      this.selectedAnimals.map(s =>
        this.apiService.crearEventoSanitario(s.cui, base as EventoSanitarioCreate)
          .pipe(catchError(() => of(null))).toPromise()
      )
    ).then(() => {
      this.submitting = false; this.closeModal();
      if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
      if (this.tablaModo === 'hato' || this.tablaModo === 'alertas') this.cargarTabla();
    });
  }

  // Producción: una por animal (obligatorio 1 seleccionado)
  submitProduccion(): void {
    if (this.selectedAnimals.length !== 1) { alert('Selecciona un (1) animal.'); return; }
    const cui = this.selectedAnimals[0].cui;
    const payload: EventoProduccionCreate = {
      fecha_evento: this.formProduccion.fecha_evento.length <= 16
        ? this.formProduccion.fecha_evento + ':00Z'
        : this.formProduccion.fecha_evento,
      // tipificamos el evento según producto; si usas PESAJE aparte, cámbialo en backend
      tipo_evento: this.formProduccion.producto as any, 
      valor: this.formProduccion.valor || null,
      observaciones: this.formProduccion.observaciones || null
    };

    this.submitting = true;
    this.apiService.crearEventoProduccion(cui, payload)
      .pipe(catchError(() => of(null)))
      .subscribe((ok) => {
        this.submitting = false;
        if (ok) {
          this.closeModal();
          if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
          this.tablaModo = 'produccion'; this.tablaTitulo = `Producción (${this.periodoProduccionLabel})`; this.cargarTabla();
        } else {
          alert('Error al registrar producción.');
        }
      });
  }

  // Control de Calidad: multi
  submitCalidad(): void {
    if (this.selectedAnimals.length === 0) { alert('Selecciona al menos un animal.'); return; }
    const fechaIso = this.formCalidad.fecha_evento.length <= 16
      ? this.formCalidad.fecha_evento + ':00Z' : this.formCalidad.fecha_evento;

    // Endpoint pendiente en ApiService/Backend. Por ahora, disparamos como eventos de producción con tag “CONTROL”
    // o deja esto como TODO si prefieres esperar el backend.
    const cuerpo = {
      fecha_evento: fechaIso,
      producto: this.formCalidad.producto,
      metodo_id: this.formCalidad.metodo_id,
      valor: this.formCalidad.valor,
      unidad_medida: this.formCalidad.unidad_medida,
      observaciones: this.formCalidad.observaciones
    };

    this.submitting = true;
    Promise.all(
      this.selectedAnimals.map(a =>
        this.apiService.crearControlCalidad(a.cui, cuerpo) // <-- añade este método en ApiService
          .pipe(catchError(() => of(null))).toPromise()
      )
    ).then(() => {
      this.submitting = false; this.closeModal();
      // refrescos:
      if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
      this.tablaModo = 'produccion'; this.cargarTabla();
    });
  }
}
