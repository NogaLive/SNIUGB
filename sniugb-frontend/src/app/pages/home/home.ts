import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.html',
  styleUrls: ['./home.css']
})
export class HomeComponent implements OnInit {
  // Esta variable guardará las categorías que vienen de la base de datos
  categorias: any[] = [];

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    // 1. Llama al backend para obtener la lista de objetos de categoría
    this.apiService.getCategorias().subscribe({
      next: (data) => {
        // 2. La data ya viene lista con 'nombre' y 'imagen_url',
        //    así que simplemente la asignamos.
        this.categorias = data;
      },
      error: (err) => console.error('Error al cargar categorías:', err)
    });
  }
}