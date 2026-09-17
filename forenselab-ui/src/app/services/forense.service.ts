import { Injectable, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

/**
 * Representa uma porta aberta descoberta pelo motor Go.
 */
export interface OpenPort {
  port: number;
  protocol: string;
  state: string;
  service: string;
  banner?: string;
  latency_ms: number;
}

/**
 * Envelope final retornado com sucesso pelo Go Core.
 */
export interface ScanDoneData {
  target: string;
  scanned_ports: number;
  open_ports: OpenPort[];
  total_open: number;
}

/**
 * Evento emitido pelo stream SSE do FastAPI/Go.
 */
export interface ScanEvent {
  event: 'started' | 'progress' | 'done' | 'error';
  job_id: string;
  // Propriedades do evento 'progress'
  type?: 'progress' | 'log';
  msg?: string;
  percent?: number;
  percent_done?: number;
  step?: number;
  total?: number;
  // Propriedades do evento 'done'
  status?: string;
  data?: {
    schema_version?: string;
    status?: string;
    command?: string;
    timestamp?: string;
    duration_ms?: number;
    data?: ScanDoneData;
  };
  // Propriedades do evento 'error'
  message?: string;
  exit_code?: number;
}

export interface AbortScanResponse {
  job_id: string;
  status: string;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ForenseService {
  private readonly baseUrl = 'http://127.0.0.1:8000/api/v1/network/scan';
  private currentEventSource: EventSource | null = null;
  private currentJobId: string | null = null;

  constructor(
    private readonly http: HttpClient,
    private readonly zone: NgZone
  ) {}

  /**
   * Dispara a varredura e conecta via Server-Sent Events (SSE).
   * Encapsulado em um Observable RxJS que opera dentro do NgZone.run().
   */
  public startScan(
    target: string,
    ports: string = '21,22,53,80,443,445,3306,8080',
    workers: number = 500,
    timeoutMs: number = 1000
  ): Observable<ScanEvent> {
    return new Observable<ScanEvent>((observer) => {
      // Fecha qualquer conexão SSE anterior se ainda ativa
      this.closeEventSource();

      const queryParams = new URLSearchParams({
        target,
        ports,
        workers: workers.toString(),
        timeout_ms: timeoutMs.toString()
      });

      const url = `${this.baseUrl}/stream?${queryParams.toString()}`;
      const eventSource = new EventSource(url);
      this.currentEventSource = eventSource;

      // 1. Evento de Inicialização ('started')
      eventSource.addEventListener('started', (event: MessageEvent) => {
        this.zone.run(() => {
          try {
            const parsed = JSON.parse(event.data) as ScanEvent;
            this.currentJobId = parsed.job_id;
            observer.next(parsed);
          } catch (err) {
            console.error('[ForenseService] Erro ao parsear evento started:', err);
          }
        });
      });

      // 2. Evento de Progresso ('progress')
      eventSource.addEventListener('progress', (event: MessageEvent) => {
        this.zone.run(() => {
          try {
            const parsed = JSON.parse(event.data) as ScanEvent;
            if (parsed.job_id && !this.currentJobId) {
              this.currentJobId = parsed.job_id;
            }
            observer.next(parsed);
          } catch (err) {
            console.error('[ForenseService] Erro ao parsear evento progress:', err);
          }
        });
      });

      // 3. Evento de Conclusão ('done')
      eventSource.addEventListener('done', (event: MessageEvent) => {
        this.zone.run(() => {
          try {
            const parsed = JSON.parse(event.data) as ScanEvent;
            observer.next(parsed);
            observer.complete();
          } catch (err) {
            console.error('[ForenseService] Erro ao parsear evento done:', err);
            observer.error(err);
          } finally {
            this.closeEventSource();
          }
        });
      });

      // 4. Evento de Erro emitido pelo backend ('error' customizado)
      eventSource.addEventListener('error', (event: any) => {
        this.zone.run(() => {
          if (event.data) {
            try {
              const parsed = JSON.parse(event.data) as ScanEvent;
              observer.next(parsed);
              if (parsed.status === 'aborted') {
                observer.complete();
                return;
              }
            } catch {}
          }
          // Falha na conexão de rede / SSE desconectado
          if (eventSource.readyState === EventSource.CLOSED) {
            observer.complete();
          } else {
            observer.error(new Error('Conexão SSE interrompida com o servidor ForenseLab.'));
          }
          this.closeEventSource();
        });
      });

      // Teardown logic do Observable: quando o consumidor der unsubscribe()
      return () => {
        this.closeEventSource();
      };
    });
  }

  /**
   * Envia requisição POST para abortar o processo Go ativo de forma atômica.
   */
  public abortScan(): Observable<AbortScanResponse> {
    if (!this.currentJobId) {
      this.closeEventSource();
      return throwError(() => new Error('Nenhum Job de varredura ativo para cancelamento.'));
    }

    const payload = { job_id: this.currentJobId };
    return this.http.post<AbortScanResponse>(`${this.baseUrl}/abort`, payload).pipe(
      catchError((error) => {
        console.warn('[ForenseService] Falha ao abortar Job no servidor:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Fecha o EventSource com segurança limpando referências locais.
   */
  public closeEventSource(): void {
    if (this.currentEventSource) {
      this.currentEventSource.close();
      this.currentEventSource = null;
    }
  }

  public getActiveJobId(): string | null {
    return this.currentJobId;
  }
}
