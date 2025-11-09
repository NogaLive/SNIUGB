import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, TitleCasePipe } from '@angular/common';
import { Router, RouterLink, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { catchError, of } from 'rxjs';

/* ===== FullCalendar (v6) ===== */
import { FullCalendarModule } from '@fullcalendar/angular';
import { CalendarOptions, EventInput } from '@fullcalendar/core';
import esLocale from '@fullcalendar/core/locales/es';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';

import {
  PredioModalComponent
} from '../../components/predio-modal/predio-modal';
import {
  ApiService,
  KPISchema,
  Recordatorio,
  ApiEvento,
  PredioResponseSchema,
  Notificacion
} from '../../services/api';
import { AuthService } from '../../services/auth';

type CentroActividadTab = 'notificaciones' | 'recordatorios';
type Periodo = 'hoy' | 'semana' | 'mes';

@Component({
  selector: 'app-user',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterModule,
    FormsModule,
    PredioModalComponent,
    DatePipe,
    TitleCasePipe,
    FullCalendarModule
  ],
  templateUrl: './user.html',
  styleUrls: ['./user.css'],
  providers: [],
})
export class UserHomeComponent implements OnInit {
  public locale: string = 'es';
  isLoading = true;
  mostrarModalCrearPredio = false;
  listaDePredios: PredioResponseSchema[] = [];
  predioActivoCodigo: string | null = null;

  // KPIs
  kpis: KPISchema | null = null;

  // Periodos para KPIs (solo afectan la tabla)
  periodoTareas: Periodo = 'hoy';
  periodoTareasLabel = 'Hoy';
  periodoProduccion: Periodo = 'hoy';
  periodoProduccionLabel = 'Hoy';
  periodoKpiProduccion: Periodo = 'hoy';

  // Tabla dinámica
  tablaModo: 'hato' | 'alertas' | 'tareas' | 'produccion' | 'transferencias' = 'hato';
  tablaTitulo = 'Mi Hato (Últimos Registros)';
  tablaCols: { key: string; label: string }[] = [];
  tablaRows: any[] = [];

  // Sidebar
  activeTab: CentroActividadTab = 'notificaciones';
  notificaciones: Notificacion[] = [];
  recordatoriosActivos: Recordatorio[] = [];

  // Calendario (FullCalendar)
  calendarViewDate: Date = new Date();
  calendarOptions!: CalendarOptions;
  fcEvents: EventInput[] = [];
  selectedDate: Date | null = null;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initCalendarOptions();
    this.cargarDatosIniciales();
  }

  /* ---------- FullCalendar setup ---------- */
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

      dateClick: (info) => {
        this.onDateClick(info.date);
      },

      datesSet: (arg) => {
        const center = new Date(arg.start);
        center.setDate(center.getDate() + 15);
        this.calendarViewDate = center;
        this.loadEventosDelMes();
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

  /* ---------------- Carga inicial ---------------- */
  cargarDatosIniciales(): void {
    this.isLoading = true;
    this.apiService.getMisPredios().pipe(
      catchError((err: any) => {
        console.error('Error fatal al cargar predios:', err);
        this.isLoading = false;
        return of([]);
      })
    ).subscribe((predios: PredioResponseSchema[]) => {
      if (predios.length === 0) {
        this.mostrarModalCrearPredio = true;
        this.isLoading = false;
      } else {
        this.listaDePredios = predios;
        this.predioActivoCodigo = predios[0].codigo_predio;
        this.cargarDatosDashboard(this.predioActivoCodigo);
        this.cargarDatosSidebar();

        // tabla por defecto
        this.tablaModo = 'hato';
        this.tablaTitulo = 'Mi Hato (Últimos Registros)';
        this.cargarTabla();
      }
    });
  }

  cargarDatosDashboard(codigoPredio: string): void {
    if (!codigoPredio) return;
    this.isLoading = true;
    this.kpis = null;

    this.apiService.getDashboardKpis(codigoPredio, this.periodoKpiProduccion).pipe(
      catchError((err: any) => {
        console.error('Error al cargar KPIs:', err);
        this.isLoading = false;
        return of(null);
      })
    ).subscribe((data: KPISchema | null) => {
      this.kpis = data;
      if (data) this.isLoading = false;
    });
  }

  cargarDatosSidebar(): void {
    this.apiService.getRecordatoriosActivos().pipe(
      catchError((err: any) => of([]))
    ).subscribe((data: Recordatorio[]) => this.recordatoriosActivos = data);

    this.apiService.getNotificaciones().pipe(
      catchError((err: any) => of([]))
    ).subscribe((data: Notificacion[]) => this.notificaciones = data);

    this.loadEventosDelMes();
  }

  /* --------- Calendario: eventos --------- */
  loadEventosDelMes(): void {
    const year = this.calendarViewDate.getFullYear();
    const month = this.calendarViewDate.getMonth() + 1;

    this.apiService.getEventosDelMes(year, month).pipe(
      catchError((err: any) => {
        console.error('Error al cargar eventos del calendario:', err);
        return of([]);
      })
    ).subscribe((eventos: ApiEvento[]) => {
      this.fcEvents = this.mapApiEventsToFC(eventos);
      this.calendarOptions = { ...this.calendarOptions, events: this.fcEvents };
    });
  }

  private mapApiEventsToFC(eventos: ApiEvento[]): EventInput[] {
    return eventos.map((e) => ({
      start: new Date(e.fecha_evento),
      title: e.titulo,
      extendedProps: { tipo: e.tipo }
    }));
  }

  /* ---------------- Interacciones ---------------- */
  onPredioCreado(_: PredioResponseSchema): void {
    this.mostrarModalCrearPredio = false;
    this.cargarDatosIniciales();
  }

  onPredioChange(): void {
    if (!this.predioActivoCodigo) return;

    if (this.predioActivoCodigo === 'CREAR_NUEVO') {
      this.predioActivoCodigo = this.listaDePredios.length > 0 ? this.listaDePredios[0].codigo_predio : null;
      this.mostrarModalCrearPredio = true;
    } else {
      this.cargarDatosDashboard(this.predioActivoCodigo);
      this.cargarTabla();
    }
  }

  /* ---- KPI handlers ---- */
  onKpiHatoClick(): void {
    this.tablaModo = 'hato';
    this.tablaTitulo = 'Mi Hato (Registro total)';
    this.cargarTabla();
  }

  onKpiAlertasClick(): void {
    this.tablaModo = 'alertas';
    this.tablaTitulo = 'Alertas de salud (Mes actual)';
    this.cargarTabla();
  }

  onKpiTareasClick(): void {
    if (this.periodoTareas === 'hoy') { this.periodoTareas = 'semana'; this.periodoTareasLabel = 'Semana'; }
    else if (this.periodoTareas === 'semana') { this.periodoTareas = 'mes'; this.periodoTareasLabel = 'Mes'; }
    else { this.periodoTareas = 'hoy'; this.periodoTareasLabel = 'Hoy'; }

    this.tablaModo = 'tareas';
    this.tablaTitulo = `Tareas Pendientes (${this.periodoTareasLabel})`;
    this.cargarTabla();
  }

  onKpiProduccionKpiClick(): void {
    if (this.periodoProduccion === 'hoy') { this.periodoProduccion = 'semana'; this.periodoProduccionLabel = 'Semana'; }
    else if (this.periodoProduccion === 'semana') { this.periodoProduccion = 'mes'; this.periodoProduccionLabel = 'Mes'; }
    else { this.periodoProduccion = 'hoy'; this.periodoProduccionLabel = 'Hoy'; }

    this.periodoKpiProduccion = this.periodoProduccion;
    if (this.predioActivoCodigo) {
      this.apiService.getDashboardKpis(this.predioActivoCodigo, this.periodoKpiProduccion)
        .pipe(catchError(() => of(null)))
        .subscribe(d => this.kpis = d);
    }

    this.tablaModo = 'produccion';
    this.tablaTitulo = `Producción (${this.periodoProduccionLabel})`;
    this.cargarTabla();
  }

  onKpiTransferenciasClick(): void {
    this.tablaModo = 'transferencias';
    this.tablaTitulo = 'Transferencias Pendientes';
    this.cargarTabla();
  }

  /* ---- Tabla dinámica ---- */
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

  /* ---- Sidebar ---- */
  seleccionarTab(tab: CentroActividadTab): void { this.activeTab = tab; }

  marcarNotificacionLeida(notif: Notificacion): void {
    if (notif.leida && !notif.link) return;
    this.apiService.marcarNotificacionLeida(notif.id).subscribe({
      next: (detalleNotif) => {
        notif.leida = true;
        if (detalleNotif.link) this.router.navigate([detalleNotif.link]);
      },
      error: (err: any) => console.error('Error al marcar notificación como leída:', err)
    });
  }

  toggleRecordatorio(recordatorio: Recordatorio): void {
    this.apiService.toggleRecordatorio(recordatorio.id).subscribe({
      next: () => this.cargarDatosSidebar(),
      error: (err: any) => console.error('Error al actualizar recordatorio:', err)
    });
  }

  /* ---- Calendario: selección y utilidades ---- */
  private sameDay(a: Date, b: Date): boolean {
    return a.getFullYear() === b.getFullYear() &&
           a.getMonth() === b.getMonth() &&
           a.getDate() === b.getDate();
  }

  onDateClick(date: Date): void {
    this.selectedDate = date;
    this.calendarOptions = { ...this.calendarOptions };
  }

  isSelected(d: Date): boolean {
    return !!this.selectedDate && this.sameDay(this.selectedDate, d);
  }

  isWeekend(d: Date): boolean {
    const w = d.getDay();
    return w === 0 || w === 6;
  }

  private hasEventsDate(date: Date): boolean {
    return this.fcEvents?.some(e => e.start && this.sameDay(new Date(e.start as any), date));
  }

  private hasReminderDate(date: Date): boolean {
    return this.fcEvents?.some(e => {
      const isSame = e.start && this.sameDay(new Date(e.start as any), date);
      const tipo = (e.extendedProps as any)?.tipo;
      return isSame && tipo === 'RECORDATORIO';
    }) || false;
  }

  cambiarMes(offset: number): void {
    const newDate = new Date(this.calendarViewDate);
    newDate.setMonth(newDate.getMonth() + offset);
    this.calendarViewDate = newDate;

    this.calendarOptions = {
      ...this.calendarOptions,
      initialDate: this.calendarViewDate
    };

    this.loadEventosDelMes();
  }

  /* ==========================
   * NUEVOS: Gestión (botones)
   * ========================== */

  goGestionSanitarioMasivo(): void {
    // Aquí luego: this.router.navigate(['/gestion/sanitario']);
    console.info('Ir a Gestión > Eventos Sanitarios (masivo)');
    alert('Eventos Sanitarios (masivo): próximamente. Aquí podrás aplicar enfermedad/tratamiento a varios animales.');
  }

  goGestionControlProduccion(): void {
    // Vista de control de producción; por ahora muestra tabla de producción del periodo actual
    this.tablaModo = 'produccion';
    this.tablaTitulo = `Producción (${this.periodoProduccionLabel})`;
    this.cargarTabla();
  }

  goGestionPesaje(): void {
    // Acceso rápido a producción tipo Pesaje (luego se navega a formulario)
    console.info('Ir a Gestión > Pesaje (individual)');
    alert('Pesaje rápido: próximamente. Permitirá registrar el peso del animal y actualizar su ficha.');
  }

  goGestionPartoGenealogia(): void {
    console.info('Ir a Gestión > Parto & Genealogía');
    alert('Parto & Genealogía: próximamente. Vinculará crías/ascendencia y mostrará el árbol (3 generaciones).');
  }

  goGestionGrupos(): void {
    console.info('Ir a Gestión > Grupos de Animales');
    alert('Grupos de Animales: próximamente. Crea grupos para selecciones masivas reutilizables.');
  }
}
