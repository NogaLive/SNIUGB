import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Articulo } from '../models/articulo.model';

export interface ArticulosResponse {
  articulos: Articulo[];
  total: number;
  page: number;
  pages: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) { }

  getCategorias(): Observable<any> {
    return this.http.get(`${this.backendUrl}/categorias/`);
  }

  getArticulos(page: number = 1, categoriaId: number | null = null): Observable<ArticulosResponse> {
    let params = new HttpParams().set('page', page.toString());

    if (categoriaId !== null) {
      params = params.set('categoria_id', categoriaId.toString());
    }

    return this.http.get<ArticulosResponse>(`${this.backendUrl}/publicaciones/`, { params });
  }

  getPublicaciones(categoria?: string): Observable<any> {
    let url = `${this.backendUrl}/publicaciones/`;
    if (categoria) {
      url += `?categoria=${categoria}`;
    }
    return this.http.get(url);
  }

}