import { Component, OnInit } from '@angular/core';
// ARREGLADO: Importamos TitleCasePipe y DatePipe
import { CommonModule, DatePipe, TitleCasePipe } from '@angular/common'; 
import { Router, RouterLink, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms'; 
import { catchError, of } from 'rxjs'; 

// --- ARREGLO DE IMPORTACIÓN (Error NG8001) ---
// Importamos solo los componentes/pipes que SÍ usamos
import { 
  CalendarEvent, 
  CalendarMonthViewComponent,
  CalendarDatePipe // <--- Para el template del día
} from 'angular-calendar';
// NO importamos DateAdapter, adapterFactory ni CalendarCommonModule aquí.
// ---------------------------------------------

import { PredioModalComponent } from '../../components/predio-modal/predio-modal';
import { 
  ApiService, 
  KPISchema, 
  Recordatorio, 
  ApiEvento, 
  PredioResponseSchema, 
  AnimalResponseSchema,
  Notificacion
} from '../../services/api';
import { AuthService } from '../../services/auth';

type CentroActividadTab = 'notificaciones' | 'recordatorios';
type KpiPeriodo = 'hoy' | 'semana' | 'mes';

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
    TitleCasePipe, // <--- Para el título del mes
    CalendarMonthViewComponent, // <--- Para <mwl-calendar-month-view>
    CalendarDatePipe          // <--- Para el pipe | calendarDate
  ],
  templateUrl: './user.html', 
  styleUrls: ['./user.css'],   
  
  // ARREGLADO: El array de providers DEBE estar vacío.
  // Todo se provee globalmente en main.ts o app.config.ts.
  providers: [], 
})
export class UserHomeComponent implements OnInit { 
  
  public locale: string = 'es'; // Correcto, el HTML lo usa
  isLoading: boolean = true;
  mostrarModalCrearPredio: boolean = false;
  listaDePredios: PredioResponseSchema[] = [];
  predioActivoCodigo: string | null = null;
  kpis: KPISchema | null = null;
  periodoKpi: KpiPeriodo = 'hoy';
  periodoKpiLabel: string = 'Hoy';
  animalesHato: AnimalResponseSchema[] = [];
  activeTab: CentroActividadTab = 'notificaciones';
  notificaciones: Notificacion[] = [];
  recordatoriosActivos: Recordatorio[] = [];
  calendarViewDate: Date = new Date();
  calendarEvents: CalendarEvent[] = [];
  
  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  // --- Lógica de Carga ---

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
      }
    });
  }

  cargarDatosDashboard(codigoPredio: string): void {
    if (!codigoPredio) return;
    
    this.isLoading = true; 
    this.kpis = null; 
    this.animalesHato = []; 
    
    this.apiService.getDashboardKpis(codigoPredio, this.periodoKpi).pipe(
      catchError((err: any) => {
        console.error('Error al cargar KPIs (ver log de backend):', err);
        this.isLoading = false;
        return of(null); 
      })
    ).subscribe((data: KPISchema | null) => { 
      this.kpis = data; 
      if (data) {
        this.isLoading = false;
      }
    });

    this.apiService.getAnimalesByPredio(codigoPredio, 'activo').pipe(
      catchError((err: any) => {
        console.error('Error al cargar animales:', err);
        return of([]); 
      })
    ).subscribe((data: AnimalResponseSchema[]) => {
      this.animalesHato = data
        .sort((a, b) => new Date(b.fecha_nacimiento).getTime() - new Date(a.fecha_nacimiento).getTime())
        .slice(0, 10); 
    });
  }
  
  cargarDatosSidebar(): void {
    this.apiService.getRecordatoriosActivos().pipe(
      catchError((err: any) => {
        console.error('Error al cargar recordatorios:', err);
        return of([]);
      })
    ).subscribe((data: Recordatorio[]) => { this.recordatoriosActivos = data; });
    
    this.apiService.getNotificaciones().pipe(
      catchError((err: any) => {
        console.error('Error al cargar notificaciones:', err);
        return of([]);
      })
    ).subscribe((data: Notificacion[]) => { this.notificaciones = data; });

    this.loadEventosDelMes();
  }

  loadEventosDelMes(): void {
    const year = this.calendarViewDate.getFullYear();
    const month = this.calendarViewDate.getMonth() + 1; 

    this.apiService.getEventosDelMes(year, month).pipe(
      catchError((err: any) => { 
        console.error('Error al cargar eventos del calendario:', err);
        return of([]); 
      })
    ).subscribe((eventos: ApiEvento[]) => { 
      this.calendarEvents = this.mapApiEventsToCalendarEvents(eventos);
    });
  }

  // --- Manejadores de Eventos ---

  onPredioCreado(nuevoPredio: PredioResponseSchema): void {
    this.mostrarModalCrearPredio = false;
    this.cargarDatosIniciales(); 
  }

  onPredioChange(): void {
    if (this.predioActivoCodigo) {
      if (this.predioActivoCodigo === 'CREAR_NUEVO') {
        this.predioActivoCodigo = this.listaDePredios.length > 0 ? this.listaDePredios[0].codigo_predio : null;
        this.mostrarModalCrearPredio = true; 
      } else {
        this.cargarDatosDashboard(this.predioActivoCodigo);
      }
    }
  }

  onKpiProduccionClick(): void {
    if (this.periodoKpi === 'hoy') {
      this.periodoKpi = 'semana';
      this.periodoKpiLabel = 'Semana Actual';
    } else if (this.periodoKpi === 'semana') {
      this.periodoKpi = 'mes';
      this.periodoKpiLabel = 'Mes Actual';
    } else {
      this.periodoKpi = 'hoy';
      this.periodoKpiLabel = 'Hoy';
    }
    
    if (this.predioActivoCodigo) {
      this.kpis = null; 
      this.apiService.getDashboardKpis(this.predioActivoCodigo, this.periodoKpi).pipe(
        catchError((err: any) => {
          console.error('Error al cargar KPIs:', err);
          return of(null);
        })
      ).subscribe((data: KPISchema | null) => { 
        this.kpis = data; 
      });
    }
  }

  seleccionarTab(tab: CentroActividadTab): void {
    this.activeTab = tab;
  }
  
  marcarNotificacionLeida(notif: Notificacion): void {
    if (notif.leida && !notif.link) return; 

    this.apiService.marcarNotificacionLeida(notif.id).subscribe({
      next: (detalleNotif) => {
        notif.leida = true; 
        if (detalleNotif.link) {
          this.router.navigate([detalleNotif.link]);
        }
      },
      error: (err: any) => console.error('Error al marcar notificación como leída:', err)
    });
  }
  
  toggleRecordatorio(recordatorio: Recordatorio): void {
    this.apiService.toggleRecordatorio(recordatorio.id).subscribe({
      next: () => {
        this.cargarDatosSidebar(); 
      },
      error: (err: any) => console.error('Error al actualizar recordatorio:', err)
    });
  }

  onDayClicked(date: Date): void {
    console.log('Día clickeado:', date);
  }

  // ARREGLADO: Esta función es necesaria para el (viewDateChange) del header
  cambiarMes(offset: number): void {
    const newDate = new Date(this.calendarViewDate);
    newDate.setMonth(newDate.getMonth() + offset);
    this.calendarViewDate = newDate;
    this.loadEventosDelMes(); 
  }
  // ------------------------------------------

  // --- Helpers ---
  public getCondicionClass(condicion: string): string {
    if (!condicion) return '';
    return condicion.toLowerCase().replace(' ', '-');
  }

  private mapApiEventsToCalendarEvents(eventos: ApiEvento[]): CalendarEvent[] {
    return eventos.map((evento) => ({
      start: new Date(evento.fecha_evento),
      title: evento.titulo,
      color: this.getEventColor(evento.tipo),
      meta: evento,
    }));
  }

  private getEventColor(tipo: string): { primary: string; secondary: string } {
    const azul = '#0056AC';
    const verde = '#128C7E';
    
    if (tipo === 'RECORDATORIO') {
      return { primary: verde, secondary: '#D9F0ED' };
    }
    return { primary: azul, secondary: '#D9E7F6' };
  }
}