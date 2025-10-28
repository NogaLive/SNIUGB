import { Component, EventEmitter, Output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
// ARREGLADO: Usamos SimpleResponse de api.ts
import { ApiService, PredioResponseSchema, SimpleResponse } from '../../services/api'; 

@Component({
  selector: 'app-predio-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './predio-modal.html',
  styleUrls: ['./predio-modal.css']
})
export class PredioModalComponent implements OnInit {
  // Evento que se emite cuando el predio se crea exitosamente
  @Output() predioCreado = new EventEmitter<PredioResponseSchema>();
  
  predioForm: FormGroup;
  departamentos: SimpleResponse[] = []; // ARREGLADO: Usamos la interfaz de api.ts
  errorMessage: string | null = null;
  isLoading: boolean = false;
  isLoadingDepartamentos: boolean = true; // Para mostrar un loader en el select

  constructor(private fb: FormBuilder, private apiService: ApiService) {
    this.predioForm = this.fb.group({
      nombre_predio: ['', [Validators.required, Validators.minLength(3)]],
      departamento: ['', Validators.required],
      ubicacion: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // ARREGLADO: Cargamos los departamentos desde la API
    this.loadDepartamentos();
  }

  loadDepartamentos(): void {
    this.isLoadingDepartamentos = true;
    // Llama al endpoint de utils.py
    this.apiService.getDepartamentos().subscribe({
      next: (data) => {
        this.departamentos = data;
        this.isLoadingDepartamentos = false;
      },
      error: (err: any) => {
        console.error("Error al cargar departamentos", err);
        this.isLoadingDepartamentos = false;
        this.errorMessage = "No se pudieron cargar los departamentos. Intente de nuevo.";
      }
    });
  }

  onSubmit(): void {
    if (this.predioForm.invalid) {
      this.errorMessage = 'Por favor, completa todos los campos.';
      return;
    }
    
    this.isLoading = true;
    this.errorMessage = null;

    // El formControlName="departamento" guardará el 'nombre' (string),
    // que es lo que espera el backend (PredioCreateSchema).
    this.apiService.crearPredio(this.predioForm.value).subscribe({
      next: (nuevoPredio) => {
        this.isLoading = false;
        // ¡Éxito! Emitimos el evento al componente padre (user.ts)
        this.predioCreado.emit(nuevoPredio);
      },
      error: (err: any) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Ocurrió un error inesperado.';
      }
    });
  }
}