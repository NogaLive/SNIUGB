import { Categoria } from './categoria.model';

export interface Autor {
  id: number;
  nombre_completo: string;
}

export interface Articulo {
  id: number;
  slug: string;
  titulo: string;
  resumen: string;
  imagen_thumbnail_url: string;
  vistas: number;
  categoria: Categoria;
  autor: Autor;
}