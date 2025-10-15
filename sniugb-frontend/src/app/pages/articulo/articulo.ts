import { Component, OnInit } from '@angular/core';
import { CommonModule, NgFor, NgIf } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { DatePipe } from '@angular/common';

import { ApiService } from '../../services/api';
import { Articulo } from '../../models/articulo.model';

@Component({
  selector: 'app-articulo',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIf, NgFor, DatePipe],
  templateUrl: './articulo.html',
  styleUrls: ['./articulo.css']
})
export class ArticuloComponent implements OnInit {

  backendUrl = 'http://127.0.0.1:8000';
  
  articulo: Articulo | null = null;
  contenidoSanitizado: SafeHtml = '';
  
  // Para la barra lateral
  articulosPopulares: Articulo[] = [];
  articulosRecientes: Articulo[] = [];
  sidebarTabActiva: 'populares' | 'recientes' = 'populares';

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    // Escucha los cambios en el 'slug' de la URL para recargar el artículo si cambia
    this.route.params.subscribe(params => {
      const slug = params['slug'];
      if (slug) {
        this.cargarArticulo(slug);
      }
    });

    this.cargarArticulosSidebar();
  }

  cargarArticulo(slug: string): void {
    this.apiService.getArticuloBySlug(slug).subscribe((data: Articulo) => {
      this.articulo = data;
      if (this.articulo) {
        // Sanitiza el contenido HTML del backend para renderizarlo de forma segura
        this.contenidoSanitizado = this.sanitizer.bypassSecurityTrustHtml(this.articulo.contenido_html);
      }
    });
  }

  cargarArticulosSidebar(): void {
    // Asumimos que el ApiService tendrá estos métodos
    this.apiService.getPopularArticles().subscribe((data: Articulo[]) => {
      this.articulosPopulares = data;
    });
    this.apiService.getRecentArticles().subscribe((data: Articulo[]) => {
      this.articulosRecientes = data;
    });
  }

  cambiarTabSidebar(tab: 'populares' | 'recientes'): void {
    this.sidebarTabActiva = tab;
  }
}