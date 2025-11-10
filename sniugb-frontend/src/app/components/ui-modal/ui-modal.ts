import { Component, ElementRef, EventEmitter, HostListener, Input, Output, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-ui-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ui-modal.html',
  styleUrls: ['./ui-modal.css']
})
export class UiModalComponent {
  /** Abierto/cerrado */
  @Input() open = false;

  /** Título del modal (barra superior) */
  @Input() title = '';

  /** Emite cuando se solicita cierre */
  @Output() requestClose = new EventEmitter<void>();

  /** Refs para la lógica de cerrar “al soltar” fuera */
  @ViewChild('overlay', { static: false }) overlayRef?: ElementRef<HTMLDivElement>;
  @ViewChild('card', { static: false }) cardRef?: ElementRef<HTMLDivElement>;

  private pointerDownOutside = false;

  // ========= Regla de cierre: solo si presiona fuera y SUELTA fuera =========
  onOverlayPointerDown(ev: PointerEvent) {
    if (!this.cardRef?.nativeElement.contains(ev.target as Node)) {
      this.pointerDownOutside = true;
    } else {
      this.pointerDownOutside = false;
    }
  }

  onOverlayPointerUp(ev: PointerEvent) {
    const upOutside = !this.cardRef?.nativeElement.contains(ev.target as Node);
    if (this.pointerDownOutside && upOutside) this.requestClose.emit();
    this.pointerDownOutside = false;
  }

  // Cancelamos la propagación dentro de la tarjeta
  stop(ev: Event) { ev.stopPropagation(); }

  // Nota: No cerramos con ESC para cumplir tu regla
  // Si en el futuro lo deseas, descomenta:
  // @HostListener('document:keydown.escape', ['$event'])
  // onEsc(_ev: Event) { this.requestClose.emit(); }
}
