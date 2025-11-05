import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';
import { Categoria } from '../../models/categoria.model';
import { Articulo } from '../../models/articulo.model';
import { TruncatePipe } from '../../pipes/truncate.pipe';

@Component({
  selector: 'app-publicaciones',
  standalone: true,
  imports: [CommonModule, RouterLink, TruncatePipe],
  templateUrl: './publicaciones.html',
  styleUrls: ['./publicaciones.css']
})
export class PublicacionesComponent implements OnInit {

  backendUrl = 'http://127.0.0.1:8000'; // URL base para construir las rutas de imágenes

  categorias: Categoria[] = [];
  articulos: Articulo[] = [];

  // --- Estado del Componente ---
  activeCategoriaId: number | null = null; // ID de la categoría activa para el filtro
  currentPage: number = 1;
  totalPages: number = 0;
  totalArticulos: number = 0;
  articulosPorPagina: number = 6; // 2 columnas x 3 filas
  pages: number[] = [];

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute, // Para leer parámetros de la URL
    private router: Router // Para actualizar la URL sin recargar
  ) {}

  ngOnInit(): void {
    this.cargarCategorias();

    // Revisa si la URL ya tiene un filtro de categoría al cargar
    this.route.queryParams.subscribe(params => {
      const categoriaId = params['categoria'] ? Number(params['categoria']) : null;
      this.activeCategoriaId = categoriaId;
      this.cargarArticulos();
    });
  }

  cargarCategorias(): void {
    this.apiService.getCategorias().subscribe(data => {
      this.categorias = data;
    });
  }

  cargarArticulos(): void {
    // Asumimos que tu API puede recibir la página y el ID de la categoría
    this.apiService.getArticulos(this.currentPage, this.activeCategoriaId).subscribe(response => {
      this.articulos = response.articulos;
      this.totalArticulos = response.total;
      this.totalPages = Math.ceil(this.totalArticulos / this.articulosPorPagina);
      // Genera el array de números de página para el HTML
      this.pages = Array.from({ length: this.totalPages }, (_, i) => i + 1);
    });
  }

  // --- Métodos de Interacción ---

  seleccionarCategoria(categoriaId: number | null): void {
    if (this.activeCategoriaId === categoriaId) return; // No hacer nada si ya está seleccionado

    this.activeCategoriaId = categoriaId;
    this.currentPage = 1; // Siempre resetea a la primera página al cambiar de filtro
    this.cargarArticulos();
    // Actualiza el parámetro 'categoria' en la URL
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { categoria: categoriaId },
      queryParamsHandling: 'merge'
    });
  }

  irAPagina(pagina: number): void {
    if (pagina < 1 || pagina > this.totalPages || pagina === this.currentPage) return;
    this.currentPage = pagina;
    this.cargarArticulos();
  }
}