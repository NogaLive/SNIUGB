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
  AnimalResponseSchema,
  TipoEventoItem,
  Transferencia
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
  | 'produccion'
  | 'calidad'
  | 'grupos'
  | 'transfer_detalle'
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
  buscarSuggestions: AnimalResponseSchema[] = [];

  formAgregar = {
    cui: '',
    nombre: '',
    sexo: 'MACHO' as 'MACHO'|'HEMBRA',
    raza: '',
    fecha_nacimiento: new Date().toISOString().slice(0,10),
  };

  // catálogos auxiliares
  razasCatalogo: string[] = [];
  prediosUsuario: PredioResponseSchema[] = [];

  // ----- Transferencias -----
  transfer = {
    destino_predio: '',
    nota: ''
  };
  transferList: any[] = [];
  transferScope: 'mine'|'incoming'|'all' = 'mine';
  selectedTransfer: Transferencia | null = null;
  transferAnimales: AnimalResponseSchema[] = [];


  // ----- Reportes -----
  reportesDisponibles: {key:string; nombre:string}[] = [];
  formReporte = { tipo: '', periodo: 'hoy' as 'hoy'|'semana'|'mes' };

  // ----- Inventario -----
  inventario: any[] = [];
  invNuevo = { nombre:'', cantidad:0, unidad:'und' };

  inventarioFiltroUnidades: string[] = [];

  get inventarioFiltrado(): any[] {
    if (!this.inventario) return [];
    if (!this.inventarioFiltroUnidades?.length) return this.inventario;
    return this.inventario.filter(i => this.inventarioFiltroUnidades.includes(i.unidad));
  }

  // Listas dinámicas
  tipoSanidadEnfermedad: TipoEventoItem[] = [];
  tipoSanidadTratamiento: TipoEventoItem[] = [];
  metodosControlCalidad: TipoEventoItem[] = [];
  unidadesMedida = ['L', 'mL', 'kg', 'g', 'lb', 'und', 'doc'];

  // ====== NUEVO: formularios normalizados ======

  // SANITARIO (masivo): ENFERMEDAD obligatoria / TRATAMIENTO opcional
  formSanitario = {
    fecha_evento_enfermedad: new Date().toISOString().slice(0,16),
    tipo_evento_enfermedad_id: null as number | null,

    fecha_evento_tratamiento: null as string | null,
    tipo_evento_tratamiento_id: null as number | null,
    nombre_tratamiento: null as string | null,

    dosis: null as number | null,
    unidad_medida_dosis: 'mL' as string | null,

    observaciones: '' as string | null
  };

  // PRODUCCIÓN (una por animal)
  formProduccion: {
    fecha_evento: string;
    producto: 'LECHE'|'CARNE'|'CUERO';
    valor: string | number | null;
    unidad_medida: string | null;
    observaciones: string | null;
    animal_cui: string | null;
  } = {
    fecha_evento: new Date().toISOString().slice(0,16),
    producto: 'LECHE',
    valor: '',
    unidad_medida: 'L',
    observaciones: '',
    animal_cui: null
  };

  produccionAnimalQuery = '';
  produccionAnimalSuggestions: AnimalResponseSchema[] = [];


  // CONTROL DE CALIDAD (multi)
  formCalidad = {
    fecha_evento: new Date().toISOString().slice(0,16),
    producto: 'LECHE' as 'LECHE'|'CARNE'|'CUERO',
    metodo_id: null as number | null, // mapea a tipo_evento_calidad_id
    valor_cantidad: null as number | null,
    unidad_medida: 'L',
    observaciones: '' as string | null
  };

  // Tablas “debajo del formulario”
  sanitariosMios: any[] = [];
  calidadMios: any[] = [];
  produccionesMias: any[] = [];

  // ----- Grupos -----
  grupos: {id:number; nombre:string; cantidad_animales: number}[] = [];
  formGrupo = { nombre:'' };
  grupoSeleccionadoId: number | null = null;

  grupoSeleccionadoNombre = '';
  grupoNuevoNombre = '';
  modoCrearGrupo = false;

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
    this.selectedAnimals = [];
    this.animalQuery = '';
    this.filtrarSugerencias('');

    // Carga de catálogos según modal
    if (key === 'agregar') {
      // Cargar catálogo de razas para el select de "Agregar ganado"
      this.apiService.getRazas()
        .pipe(catchError(() => of([])))
        .subscribe(data => {
          this.razasCatalogo = data || [];
        });
    }

    if (key === 'sanitario') {
      this.apiService.getTiposEventoByGrupo('ENFERMEDAD')
        .pipe(catchError(() => of([])))
        .subscribe((ops) => this.tipoSanidadEnfermedad = ops || []);
      this.apiService.getTiposEventoByGrupo('TRATAMIENTO')
        .pipe(catchError(() => of([])))
        .subscribe((ops) => this.tipoSanidadTratamiento = ops || []);
      this.cargarTablaSanitarios();
    } else if (key === 'calidad') {
      this.apiService.getTiposEventoByGrupo('CONTROL_CALIDAD')
        .pipe(catchError(() => of([])))
        .subscribe((ops) => this.metodosControlCalidad = ops || []);
      this.cargarTablaControlCalidad();
    } else if (key === 'produccion') {
      this.cargarTablaProduccion();
    } else if (key === 'transferencias') {
      this.cargarTransferencias();
      // Predios del usuario, excluyendo el predio activo
      this.prediosUsuario = this.listaDePredios.filter(p => p.codigo_predio !== this.predioActivoCodigo);
    } else if (key === 'reportes') {
      this.apiService.getReportesDisponibles().pipe(catchError(()=>of([]))).subscribe(list=>{
        this.reportesDisponibles = list || [];
        if (!this.formReporte.tipo && list?.length) this.formReporte.tipo = list[0].key;
      });
    } else if (key === 'inventario') {
      this.cargarInventario();
    } else if (key === 'grupos') {
      this.cargarGrupos();
    }
  }
  closeModal() { this.activeModal = null; this.submitting = false; }

  // Panel de control
  goBuscarRegistro() { this.openModal('buscar'); }
  goAgregarGanado()   { this.openModal('agregar'); }
  goTransferencias()  { this.openModal('transferencias'); }
  goReportes()        { this.openModal('reportes'); }
  goInventario()      { this.openModal('inventario'); }

  // Panel de gestión
  goGestionSanitarioMasivo() { this.openModal('sanitario'); }
  goGestionEventosProduccion() { this.openModal('produccion'); }
  goGestionControlCalidad()   { this.openModal('calidad'); }
  goGestionGrupos()           { this.openModal('grupos'); }

  /* ====== Buscador con chips (animales) ====== */
  filtrarSugerencias(q: string) {
    const query = (q || '').trim().toLowerCase();

    // Si no hay texto, no mostramos sugerencias (queda lista vacía)
    if (!query) {
      this.animalSuggestions = [];
      return;
    }

    this.animalSuggestions = (this.cachedAnimales || [])
      .filter(a =>
        !this.selectedAnimals.find(s => s.cui === a.cui) &&
        (
          a.cui.toLowerCase().includes(query) ||
          (a.nombre || '').toLowerCase().includes(query)
        )
      )
      .slice(0, 10);
  }

  onAnimalQueryChange() { this.filtrarSugerencias(this.animalQuery); }

  onBuscarCuiChange(): void {
    const q = (this.formBuscar.cui || '').trim();
    if (!q) {
      this.buscarSuggestions = [];
      return;
    }
    // Reutilizamos animales ya cacheados del predio activo
    this.buscarSuggestions = (this.cachedAnimales || [])
      .filter(a =>
        a.cui.toLowerCase().includes(q.toLowerCase()) ||
        (a.nombre || '').toLowerCase().includes(q.toLowerCase())
      )
      .slice(0, 10);
  }

  seleccionarBuscarCui(a: AnimalResponseSchema): void {
    this.formBuscar.cui = a.cui;
    this.buscarSuggestions = [];
  }

  private setSingleAnimal(a: AnimalResponseSchema) {
    this.selectedAnimals = [{ cui: a.cui, nombre: a.nombre || a.cui }];
  }

  addAnimal(a: AnimalResponseSchema) {
    if (this.activeModal === 'produccion') {
      // fuerza selección única para producción
      this.setSingleAnimal(a);
    } else {
      if (!this.selectedAnimals.find(s => s.cui === a.cui)) {
        this.selectedAnimals.push({ cui: a.cui, nombre: a.nombre || a.cui });
      }
    }
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

  // 2) Agregar Ganado
  submitAgregarGanado(): void {
    if (!this.predioActivoCodigo) { alert('Selecciona un predio.'); return; }
    const body = {
      cui: this.formAgregar.cui.trim(),
      nombre: this.formAgregar.nombre || null,
      sexo: this.formAgregar.sexo,
      raza: this.formAgregar.raza,
      fecha_nacimiento: this.formAgregar.fecha_nacimiento,
      predio_codigo: this.predioActivoCodigo
    };
    if (!body.cui) { alert('CUI es obligatorio.'); return; }

    this.submitting = true;
    this.apiService.crearAnimal(body).pipe(catchError(()=>of(null))).subscribe(res=>{
      this.submitting = false;
      if (!res) return alert('No se pudo crear el animal.');
      this.closeModal();
      this.precargarAnimalesDelPredio();
      this.cargarTabla();
    });
  }

  // 3) Transferencias
  cargarTransferencias(): void {
    this.apiService.listarTransferencias(this.transferScope).pipe(catchError(()=>of([]))).subscribe(list=>{
      this.transferList = list || [];
    });
  }
  crearTransferencia(): void {
    if (!this.predioActivoCodigo) return alert('Selecciona un predio.');
    if (this.selectedAnimals.length === 0) return alert('Selecciona al menos un animal.');
    if (!this.transfer.destino_predio) return alert('Ingresa código de predio destino.');

    const body = {
      origen_predio: this.predioActivoCodigo,
      destino_predio: this.transfer.destino_predio,
      animal_cuis: this.selectedAnimals.map(a=>a.cui),
      nota: this.transfer.nota || null
    };
    this.submitting = true;
    this.apiService.crearTransferencia(body).pipe(catchError(()=>of(null))).subscribe(ok=>{
      this.submitting = false;
      if (!ok) return alert('No se pudo crear la transferencia.');
      this.cargarTransferencias();
      this.selectedAnimals = [];
      this.animalQuery = '';
      this.filtrarSugerencias('');
      if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
      this.tablaModo = 'transferencias'; this.tablaTitulo='Transferencias Pendientes'; this.cargarTabla();
    });
  }
  aprobarTransf(t: any){ this.apiService.aprobarTransferencia(t.id).subscribe(()=>this.cargarTransferencias()); }
  rechazarTransf(t: any){ this.apiService.rechazarTransferencia(t.id).subscribe(()=>this.cargarTransferencias()); }
  cancelarTransf(t: any){ this.apiService.cancelarTransferencia(t.id).subscribe(()=>this.cargarTransferencias()); }

  verDetalleTransferencia(t: Transferencia): void {
    this.selectedTransfer = t;
    this.transferAnimales = [];

    this.submitting = true;
    this.apiService.obtenerDetalleTransferencia(t.id)
      .pipe(catchError(() => of([])))
      .subscribe((list: AnimalResponseSchema[]) => {
        this.submitting = false;
        this.transferAnimales = list || [];
        this.activeModal = 'transfer_detalle';
      });
  }

  // 4) Reportes
  descargarReporte(): void {
    if (!this.predioActivoCodigo) return;
    const req = { tipo: this.formReporte.tipo, predio: this.predioActivoCodigo, periodo: this.formReporte.periodo };
    this.submitting = true;
    this.apiService.generarReporte(req).subscribe({
      next: (blob: any) => {
        this.submitting = false;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `${req.tipo}-${req.predio}-${req.periodo}.csv`;
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
      },
      error: () => { this.submitting = false; alert('No se pudo generar el reporte.'); }
    });
  }

  // 5) Inventario
  cargarInventario(): void {
    if (!this.predioActivoCodigo) return;
    this.apiService.getInventario(this.predioActivoCodigo).pipe(catchError(()=>of([]))).subscribe(list=> this.inventario = list || []);
  }
  crearInventario(): void {
    if (!this.predioActivoCodigo) return;
    const item = { predio: this.predioActivoCodigo, nombre: this.invNuevo.nombre, cantidad: this.invNuevo.cantidad, unidad: this.invNuevo.unidad };
    if (!item.nombre) return alert('Nombre requerido.');
    this.submitting = true;
    this.apiService.crearInventarioItem(item).pipe(catchError(()=>of(null))).subscribe(ok=>{
      this.submitting = false;
      if (!ok) return alert('No se pudo crear.');
      this.invNuevo = { nombre:'', cantidad:0, unidad:'und' };
      this.cargarInventario();
    });
  }
  actualizarInventario(i: any){ this.apiService.actualizarInventarioItem(i.id, i).subscribe(()=>this.cargarInventario()); }
  eliminarInventario(i: any){ this.apiService.eliminarInventarioItem(i.id).subscribe(()=>this.cargarInventario()); }

  // 6) Evento Sanitario (masivo)
  private toIsoOrNull(v: string | null) {
    if (!v) return null;
    return v.length <= 16 ? v + ':00Z' : v;
  }

  /** Convierte un ISO completo a valor compatible con <input type="datetime-local"> (YYYY-MM-DDTHH:mm) */
  private fromIsoToLocalInput(v: string | null | undefined): string {
    if (!v) return '';
    // Si viene con zona horaria / segundos, recortamos a los primeros 16 caracteres.
    return v.toString().slice(0, 16);
  }

  submitSanitario(): void {
    if (this.selectedAnimals.length === 0) { alert('Selecciona al menos un animal.'); return; }
    if (!this.formSanitario.tipo_evento_enfermedad_id) { alert('Selecciona la ENFERMEDAD.'); return; }

    const payloadMasivo = {
      fecha_evento_enfermedad: this.toIsoOrNull(this.formSanitario.fecha_evento_enfermedad)!,
      tipo_evento_enfermedad_id: this.formSanitario.tipo_evento_enfermedad_id!,
      fecha_evento_tratamiento: this.toIsoOrNull(this.formSanitario.fecha_evento_tratamiento),
      tipo_evento_tratamiento_id: this.formSanitario.tipo_evento_tratamiento_id ?? null,
      nombre_tratamiento: this.formSanitario.nombre_tratamiento ?? null,
      dosis: this.formSanitario.dosis ?? null,
      unidad_medida_dosis: this.formSanitario.unidad_medida_dosis ?? null,
      observaciones: (this.formSanitario.observaciones || '').trim() || null,
      animales_cui: this.selectedAnimals.map(a => a.cui)
    };

    this.submitting = true;

    // Preferir método MASIVO, si existe
    const svc: any = this.apiService as any;
    const p$ = typeof svc.crearEventoSanitarioMasivo === 'function'
      ? svc.crearEventoSanitarioMasivo(payloadMasivo)
      : // Fallback (por-animal) si tu ApiService aún no tiene el masivo
        // ⚠️ Esta ruta legacy probablemente no soporte la nueva estructura;
        // se deja como "mejor esfuerzo" para no romper el build.
        of(null);

    p$.pipe(catchError(() => of(null))).subscribe((ok: any) => {
      this.submitting = false;
      if (!ok) { alert('No se pudo guardar el evento sanitario.'); return; }
      this.closeModal();
      if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
      this.cargarTablaSanitarios();
    });
  }

  // 7) Producción: una por animal
  submitProduccion(): void {
    if (this.selectedAnimals.length !== 1) { alert('Selecciona un (1) animal.'); return; }
    const cui = this.selectedAnimals[0].cui;

    const isoFecha = this.formProduccion.fecha_evento.length <= 16
      ? this.formProduccion.fecha_evento + ':00Z'
      : this.formProduccion.fecha_evento;

    const valorNum = this.formProduccion.valor !== null && this.formProduccion.valor !== ''
      ? Number(this.formProduccion.valor)
      : null;

    const payload = {
      fecha_evento: isoFecha,
      producto: this.formProduccion.producto,   // 👈 CAMBIO: producto en vez de tipo_evento
      valor: valorNum,                          // number | null
      unidad_medida: this.formProduccion.unidad_medida || null,
      observaciones: this.formProduccion.observaciones || null
    };

    this.submitting = true;
    this.apiService.crearEventoProduccion(cui, payload as any)
      .pipe(catchError(() => of(null)))
      .subscribe((ok) => {
        this.submitting = false;
        if (ok) {
          this.closeModal();
          if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
          this.tablaModo = 'produccion'; this.tablaTitulo = `Producción (${this.periodoProduccionLabel})`; this.cargarTabla();
          this.cargarTablaProduccion();
        } else {
          alert('Error al registrar producción.');
        }
      });
  }

  onProduccionAnimalChange(): void {
    const q = (this.produccionAnimalQuery || '').trim();
    if (!q) {
      this.produccionAnimalSuggestions = [];
      this.selectedAnimals = [];
      return;
    }

    this.produccionAnimalSuggestions = (this.cachedAnimales || [])
      .filter(a =>
        a.cui.toLowerCase().includes(q.toLowerCase()) ||
        (a.nombre || '').toLowerCase().includes(q.toLowerCase())
      )
      .slice(0, 10);
  }

  seleccionarProduccionAnimal(a: AnimalResponseSchema): void {
    // Un solo animal para producción
    this.selectedAnimals = [{ cui: a.cui, nombre: a.nombre || a.cui }];
    this.formProduccion.animal_cui = a.cui;
    this.produccionAnimalQuery = `${a.cui} — ${a.nombre || 'Sin nombre'}`;
    this.produccionAnimalSuggestions = [];
  }

  // 8) Control de Calidad: multi
  submitCalidad(): void {
    if (this.selectedAnimals.length === 0) { alert('Selecciona al menos un animal.'); return; }
    if (!this.formCalidad.metodo_id) { alert('Selecciona el método de control.'); return; }
    const fechaIso = this.formCalidad.fecha_evento.length <= 16
      ? this.formCalidad.fecha_evento + ':00Z' : this.formCalidad.fecha_evento;

    const payloadMasivo = {
      fecha_evento: fechaIso,
      tipo_evento_calidad_id: this.formCalidad.metodo_id!,
      producto: this.formCalidad.producto,
      valor_cantidad: this.formCalidad.valor_cantidad ?? null,
      unidad_medida: this.formCalidad.unidad_medida ?? null,
      observaciones: (this.formCalidad.observaciones || '').trim() || null,
      animales_cui: this.selectedAnimals.map(a => a.cui),
    };

    this.submitting = true;

    const svc: any = this.apiService as any;
    const p$ = typeof svc.crearControlCalidadMasivo === 'function'
      ? svc.crearControlCalidadMasivo(payloadMasivo)
      : of(null);

    p$.pipe(catchError(() => of(null))).subscribe((ok: any) => {
      this.submitting = false;
      if (!ok) { alert('No se pudo guardar el control de calidad.'); return; }
      this.closeModal();
      if (this.predioActivoCodigo) this.cargarDatosDashboard(this.predioActivoCodigo);
      this.cargarTablaControlCalidad();
    });
  }

  //EDITAR
  editarEventoSanitario(reg: any): void {
    if (!reg) { return; }
    // Mantiene el modal sanitario abierto y rellena el formulario con el registro seleccionado
    this.activeModal = 'sanitario';
    this.formSanitario.fecha_evento_enfermedad = this.fromIsoToLocalInput(reg.fecha_evento_enfermedad);
    this.formSanitario.fecha_evento_tratamiento = this.fromIsoToLocalInput(reg.fecha_evento_tratamiento);
    this.formSanitario.tipo_evento_enfermedad_id = reg.tipo_evento_enfermedad_id ?? null;
    this.formSanitario.tipo_evento_tratamiento_id = reg.tipo_evento_tratamiento_id ?? null;
    this.formSanitario.dosis = reg.dosis ?? null;
    this.formSanitario.unidad_medida_dosis = reg.unidad_medida_dosis ?? this.formSanitario.unidad_medida_dosis;
    this.formSanitario.observaciones = reg.observaciones || '';

    if (Array.isArray(reg.animales_cui)) {
      this.selectedAnimals = reg.animales_cui.map((cui: string) => ({ cui, nombre: '' }));
    } else {
      this.selectedAnimals = [];
    }
  }

  editarEventoProduccion(reg: any): void {
    if (!reg) { return; }
    this.activeModal = 'produccion';
    this.formProduccion.fecha_evento = this.fromIsoToLocalInput(reg.fecha_evento);
    // En la tabla puede venir como 'tipo_evento' o 'producto'
    this.formProduccion.producto = (reg.producto || reg.tipo_evento || this.formProduccion.producto) as any;
    this.formProduccion.valor = reg.valor_cantidad ?? reg.valor ?? this.formProduccion.valor;
    this.formProduccion.unidad_medida = reg.unidad_medida || this.formProduccion.unidad_medida;
    this.formProduccion.observaciones = reg.observaciones || '';

    if (reg.animal_cui) {
      this.selectedAnimals = [{ cui: reg.animal_cui, nombre: '' }];
      this.formProduccion.animal_cui = reg.animal_cui;
    } else {
      this.selectedAnimals = [];
      this.formProduccion.animal_cui = null;
    }
  }

  editarEventoCalidad(reg: any): void {
    if (!reg) { return; }
    this.activeModal = 'calidad';
    this.formCalidad.fecha_evento = this.fromIsoToLocalInput(reg.fecha_evento);
    this.formCalidad.producto = (reg.producto || this.formCalidad.producto) as any;
    this.formCalidad.metodo_id = reg.tipo_evento_calidad_id ?? reg.metodo_id ?? this.formCalidad.metodo_id;
    this.formCalidad.valor_cantidad = reg.valor_cantidad ?? this.formCalidad.valor_cantidad;
    this.formCalidad.unidad_medida = reg.unidad_medida || this.formCalidad.unidad_medida;
    this.formCalidad.observaciones = reg.observaciones || '';

    if (Array.isArray(reg.animales_cui)) {
      this.selectedAnimals = reg.animales_cui.map((cui: string) => ({ cui, nombre: '' }));
    } else {
      this.selectedAnimals = [];
    }
  }

  // 9) Tablas “mis eventos”
  cargarTablaSanitarios() {
    const svc: any = this.apiService as any;
    if (typeof svc.listarEventosSanitariosMios === 'function') {
      svc.listarEventosSanitariosMios().pipe(catchError(()=>of([]))).subscribe((d: any[]) => this.sanitariosMios = d || []);
    } else {
      this.sanitariosMios = [];
    }
  }
  cargarTablaControlCalidad() {
    const svc: any = this.apiService as any;
    if (typeof svc.listarControlesCalidadMios === 'function') {
      svc.listarControlesCalidadMios().pipe(catchError(()=>of([]))).subscribe((d: any[]) => this.calidadMios = d || []);
    } else {
      this.calidadMios = [];
    }
  }
  cargarTablaProduccion() {
    const svc: any = this.apiService as any;
    if (typeof svc.listarEventosProduccionMios === 'function') {
      svc.listarEventosProduccionMios().pipe(catchError(()=>of([]))).subscribe((d: any[]) => this.produccionesMias = d || []);
    } else {
      this.produccionesMias = [];
    }
  }

  // 10) Grupos
  cargarGrupos(): void {
    if (!this.predioActivoCodigo) return;
    this.apiService.listarGrupos(this.predioActivoCodigo).pipe(catchError(()=>of([]))).subscribe(list=>{
      this.grupos = (list || []).map((g: any) => ({
        id: g.id,
        nombre: g.nombre,
        cantidad_animales: g.cantidad_animales ?? 0
      }));
      if (!this.grupoSeleccionadoId && this.grupos.length) this.grupoSeleccionadoId = this.grupos[0].id;
    });
  }
  crearGrupo(): void {
    if (!this.predioActivoCodigo) return;
    if (!this.formGrupo.nombre.trim()) return alert('Nombre del grupo requerido.');
    this.submitting = true;
    this.apiService.crearGrupo(this.formGrupo.nombre.trim(), this.predioActivoCodigo)
      .pipe(catchError(()=>of(null))).subscribe(ok=>{
        this.submitting = false;
        if (!ok) return alert('No se pudo crear el grupo.');
        this.formGrupo.nombre=''; this.cargarGrupos();
      });
  }
  addMiembrosGrupo(): void {
    if (!this.grupoSeleccionadoId) return alert('Selecciona un grupo.');
    if (this.selectedAnimals.length===0) return alert('Selecciona animales.');
    const cuis = this.selectedAnimals.map(a=>a.cui);
    this.submitting = true;
    this.apiService.addMiembrosGrupo(this.grupoSeleccionadoId, cuis).pipe(catchError(()=>of(null))).subscribe(ok=>{
      this.submitting = false;
      if (!ok) return alert('No se pudo agregar.');
      this.selectedAnimals=[]; this.animalQuery=''; this.filtrarSugerencias('');
    });
  }

  onGrupoChange(): void {
    if (this.grupoSeleccionadoNombre === '__nuevo__') {
      this.modoCrearGrupo = true;
      this.grupoNuevoNombre = '';
    } else {
      this.modoCrearGrupo = false;
      this.grupoNuevoNombre = '';
    }
  }

  guardarGrupo(): void {
    const nombre = this.modoCrearGrupo ? this.grupoNuevoNombre.trim() : this.grupoSeleccionadoNombre;
    if (!nombre) return alert('Ingresa o selecciona un nombre de grupo.');
    // Aquí crear o actualizar grupo según exista o no
  }

  // ====== NUEVOS MÉTODOS: editar / eliminar grupo ======
  editarGrupo(g: any): void {
    if (!g) { return; }
    this.grupoSeleccionadoNombre = g.nombre;
    this.modoCrearGrupo = false;
    this.grupoNuevoNombre = '';
    this.grupoSeleccionadoId = g.id ?? this.grupoSeleccionadoId;
    console.log('Editando grupo:', g.nombre);
    // Si quisieras, aquí podrías cargar miembros del grupo usando getMiembrosGrupo(g.id)
  }

  eliminarGrupo(g: any): void {
    if (!g || !g.id) return;

    if (!confirm(`¿Estás seguro de que deseas eliminar el grupo "${g.nombre}"?`)) {
      return;
    }

    this.submitting = true;
    this.apiService.eliminarGrupo(g.id).pipe(
      catchError((err) => {
        console.error('Error al eliminar grupo:', err);
        alert('No se pudo eliminar el grupo.');
        return of(null);
      })
    ).subscribe(ok => {
      this.submitting = false;
      if (ok) {
        alert('Grupo eliminado correctamente.');
        this.cargarGrupos();
      }
    });
  }
}