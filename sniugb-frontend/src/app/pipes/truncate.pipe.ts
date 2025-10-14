import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  standalone: true
})
export class TruncatePipe implements PipeTransform {
  transform(value: string, limit: number = 100, trail: string = '...'): string {
    if (!value) {
      return '';
    }

    if (value.length <= limit) {
      return value;
    }

    // Corta el texto al límite de caracteres
    let truncated = value.substring(0, limit);

    // SOLUCIÓN: Usa una expresión regular para eliminar cualquier puntuación
    // o espacio al final del texto cortado (.,;:)
    truncated = truncated.replace(/[.,;:\s]+$/, '');

    return truncated + trail;
  }
}