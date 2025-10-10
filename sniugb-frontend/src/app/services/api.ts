import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) { }

  // Obtiene la lista de artículos, con un filtro opcional
  getPublicaciones(categoria?: string): Observable<any> {
    let url = `${this.backendUrl}/publicaciones`;
    if (categoria) {
      url += `?categoria=${categoria}`;
    }
    return this.http.get(url);
  }

  // Obtiene la lista de nombres de categorías únicas
  getCategorias(): Observable<string[]> {
    return this.http.get<string[]>(`${this.backendUrl}/publicaciones/categorias`);
  }
}