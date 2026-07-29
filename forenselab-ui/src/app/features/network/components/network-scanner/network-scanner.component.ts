import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NetworkService } from '../../services/network.service';

@Component({
  selector: 'app-network-scanner',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div [class.fixed]="isFullscreen" [class.inset-0]="isFullscreen" [class.z-50]="isFullscreen" [class.w-full]="isFullscreen" [class.h-full]="isFullscreen" 
         class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col transition-all duration-300">
      
      <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-bold">Network Scanner</h2>
        <button (click)="toggleFullscreen()" class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded">
          {{ isFullscreen ? 'Close Fullscreen' : 'Fullscreen' }}
        </button>
      </div>

      <div class="flex flex-col gap-3 p-4">
        <input [(ngModel)]="target" type="text" placeholder="Target IP" class="p-2 border rounded dark:bg-gray-900 dark:border-gray-600 dark:text-white">
        <input [(ngModel)]="ports" type="text" placeholder="Ports (e.g. 80,443)" class="p-2 border rounded dark:bg-gray-900 dark:border-gray-600 dark:text-white">
        <button (click)="scan()" class="bg-green-500 hover:bg-green-600 text-white font-semibold p-2 rounded">Scan</button>
      </div>

      <div class="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 p-4 m-4 rounded border border-gray-200 dark:border-gray-700">
        <pre class="text-sm font-mono whitespace-pre-wrap" *ngIf="result">{{ result | json }}</pre>
        <div *ngIf="loading" class="text-sm text-gray-500 dark:text-gray-400">Scanning...</div>
      </div>
    </div>
  `
})
export class NetworkScannerComponent {
  target = '';
  ports = '';
  result: any = null;
  loading = false;
  isFullscreen = false;

  constructor(private networkService: NetworkService) {}

  toggleFullscreen() {
    this.isFullscreen = !this.isFullscreen;
  }

  scan() {
    this.loading = true;
    this.result = null;
    const portList = this.ports ? this.ports.split(',').map(p => parseInt(p.trim(), 10)).filter(p => !isNaN(p)) : undefined;
    this.networkService.scan({ target: this.target, ports: portList }).subscribe({
      next: (res) => {
        this.result = res;
        this.loading = false;
      },
      error: (err) => {
        this.result = { error: err.message };
        this.loading = false;
      }
    });
  }
}
