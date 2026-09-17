import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import {
  ForenseService,
  OpenPort,
  ScanDoneData,
  ScanEvent
} from '../../services/forense.service';

export type ScanStatus = 'idle' | 'scanning' | 'completed' | 'aborted' | 'error';

@Component({
  selector: 'app-scan-widget',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './scan-widget.component.html',
  styleUrls: ['./scan-widget.component.css']
})
export class ScanWidgetComponent implements OnDestroy {
  // Parâmetros de Entrada
  public target: string = '127.0.0.1';
  public ports: string = '21,22,53,80,443,445,3306,8080';
  public workers: number = 500;
  public timeoutMs: number = 1000;

  // Estados Reativos do Dashboard
  public status: ScanStatus = 'idle';
  public currentJobId: string = '';
  public progressPercent: number = 0;
  public progressMsg: string = 'Pronto para iniciar varredura.';
  public durationMs: number = 0;
  public openPorts: OpenPort[] = [];
  public totalOpen: number = 0;
  public errorMessage: string = '';

  // Gerenciamento de Ciclo de Vida e Prevenção de Memory Leaks
  private readonly destroy$ = new Subject<void>();

  constructor(private readonly forenseService: ForenseService) {}

  /**
   * Dispara a varredura reativa conectando ao backend SSE.
   */
  public startScan(): void {
    if (!this.target.trim()) {
      this.errorMessage = 'Informe um alvo válido (IP ou Hostname).';
      this.status = 'error';
      return;
    }

    this.status = 'scanning';
    this.progressPercent = 0;
    this.progressMsg = `Conectando ao núcleo Go Core para escanear ${this.target}...`;
    this.openPorts = [];
    this.totalOpen = 0;
    this.errorMessage = '';
    this.durationMs = 0;

    this.forenseService
      .startScan(this.target, this.ports, this.workers, this.timeoutMs)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (evt: ScanEvent) => {
          this.handleScanEvent(evt);
        },
        error: (err: any) => {
          console.error('[ScanWidget] Erro no stream SSE:', err);
          this.status = 'error';
          this.errorMessage = err.message || 'Falha na comunicação em tempo real com o servidor.';
        },
        complete: () => {
          if (this.status === 'scanning') {
            this.status = 'completed';
          }
        }
      });
  }

  /**
   * Processa cada evento emitido pelo SSE do Go Core / FastAPI.
   */
  private handleScanEvent(evt: ScanEvent): void {
    if (evt.job_id) {
      this.currentJobId = evt.job_id;
    }

    switch (evt.event) {
      case 'started':
        this.progressMsg = `Varredura iniciada no Job ${evt.job_id}...`;
        break;

      case 'progress':
        if (evt.percent !== undefined) {
          this.progressPercent = Math.min(100, Math.max(0, Math.round(evt.percent)));
        } else if (evt.percent_done !== undefined) {
          this.progressPercent = Math.min(100, Math.max(0, Math.round(evt.percent_done)));
        }
        if (evt.msg) {
          this.progressMsg = evt.msg;
        }
        break;

      case 'done':
        this.status = 'completed';
        this.progressPercent = 100;
        this.progressMsg = 'Varredura finalizada com sucesso!';

        // Extração dos dados normalizados do Go
        const envelope = evt.data;
        if (envelope) {
          this.durationMs = envelope.duration_ms || 0;
          const scanData = envelope.data as ScanDoneData | undefined;
          if (scanData && Array.isArray(scanData.open_ports)) {
            this.openPorts = scanData.open_ports;
            this.totalOpen = scanData.total_open ?? scanData.open_ports.length;
          }
        }
        break;

      case 'error':
        if (evt.status === 'aborted') {
          this.status = 'aborted';
          this.progressMsg = 'Varredura cancelada pelo operador.';
        } else {
          this.status = 'error';
          this.errorMessage = evt.message || 'Erro durante a execução do scan.';
        }
        break;
    }
  }

  /**
   * Solicita o encerramento forçado do processo Go ao backend (Graceful Abort).
   */
  public abortScan(): void {
    if (this.status !== 'scanning') {
      return;
    }

    this.progressMsg = 'Enviando sinal de encerramento gracioso (SIGTERM)...';
    this.forenseService
      .abortScan()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (resp) => {
          this.status = 'aborted';
          this.progressMsg = `Processo ${resp.job_id} abortado com sucesso.`;
        },
        error: (err) => {
          console.warn('[ScanWidget] Falha na requisição de abort:', err);
          this.status = 'aborted';
          this.progressMsg = 'Varredura interrompida localmente.';
        }
      });
  }

  /**
   * Limpeza de ciclo de vida para garantir zero memory leaks.
   */
  public ngOnDestroy(): void {
    this.forenseService.closeEventSource();
    this.destroy$.next();
    this.destroy$.complete();
  }
}
