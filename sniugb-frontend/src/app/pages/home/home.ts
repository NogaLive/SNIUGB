import { Component, OnInit, AfterViewInit, OnDestroy, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

// Importa los módulos de Swiper que necesitas. Autoplay se mantiene.
import Swiper from 'swiper';
import { Navigation, Autoplay } from 'swiper/modules';

// Registra los módulos
Swiper.use([Navigation, Autoplay]);

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.html',
  styleUrls: ['./home.css'],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class HomeComponent implements OnInit, AfterViewInit, OnDestroy {
  
  backendUrl = 'http://127.0.0.1:8000';
  categorias: any[] = [];
  private swiperInstance: Swiper | undefined;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.apiService.getCategorias().subscribe({
      next: (data) => {
        this.categorias = data;
      },
      error: (err) => console.error('Error al cargar categorías:', err)
    });
  }

  ngAfterViewInit(): void {
    // El retraso asegura que el *ngFor de Angular haya terminado de crear los elementos en el DOM.
    setTimeout(() => this.initSwiper(), 0);
  }

  initSwiper(): void {
    // Evita reinicializar si ya existe una instancia.
    if (this.swiperInstance) return;

    this.swiperInstance = new Swiper('.swiper-container', {
      // ===================================================================
      // CONFIGURACIÓN RESPONSIVE COMPLETA Y CORREGIDA
      // ===================================================================

      // 'loop: false' es crucial para que los botones desaparezcan en los extremos.
      loop: false,

      // Se mantiene la funcionalidad de autoplay.
      autoplay: {
        delay: 7000,
        disableOnInteraction: false,
        pauseOnMouseEnter: true,
      },

      // Habilita los botones de navegación.
      navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
      },

      // --- LÓGICA RESPONSIVE CON BREAKPOINTS ---
      // Se define un comportamiento base para la vista más pequeña (móvil).
      slidesPerView: 1,
      spaceBetween: 20, // Espacio reducido para móviles.

      // 'breakpoints' define cómo cambiará el carrusel en diferentes anchos de pantalla.
      breakpoints: {
        // Cuando la pantalla mida 640px o más
        640: {
          slidesPerView: 2, // Se mostrarán 2 tarjetas
          spaceBetween: 30, // Con 30px de espacio
        },
        // Cuando la pantalla mida 1024px o más
        1024: {
          slidesPerView: 3, // Se mostrarán 3 tarjetas
          spaceBetween: 30,
        },
        // Cuando la pantalla mida 1400px o más (máxima resolución)
        1400: {
          slidesPerView: 4, // Se mostrarán 4 tarjetas
          spaceBetween: 40, // Con 40px de espacio, como solicitaste.
        }
      }
    });
  }

  ngOnDestroy(): void {
    // Buena práctica: Destruye la instancia de Swiper para evitar fugas de memoria al salir del componente.
    this.swiperInstance?.destroy();
  }
}