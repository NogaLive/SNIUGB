import { Categoria } from './categoria.model';
import { Autor } from './autor.model';

export interface Articulo {
  id: number;
  slug: string;
  titulo: string;
  resumen: string;
  imagen_display_url: string;
  imagen_thumbnail_url: string;
  fecha_publicacion: string;
  contenido_html: string;
  vistas: number;
  categoria: Categoria;
  autor: Autor;
}