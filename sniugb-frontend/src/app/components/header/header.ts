import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
// --- 1. Importa las directivas del Router ---
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-header',
  standalone: true,
  // --- 2. Añádelas a la lista de imports ---
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './header.html',
  styleUrls: ['./header.css']
})
export class HeaderComponent {

}