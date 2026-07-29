import { Component } from '@angular/core';
import { CdkDragDrop, moveItemInArray, DragDropModule } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { NetworkScannerComponent } from '../../features/network/components/network-scanner/network-scanner.component';

@Component({
  selector: 'app-dynamic-grid',
  standalone: true,
  imports: [CommonModule, DragDropModule, NetworkScannerComponent],
  template: `
    <div cdkDropList class="grid grid-cols-1 lg:grid-cols-2 gap-6" (cdkDropListDropped)="drop($event)">
      <div *ngFor="let item of items" cdkDrag class="relative bg-white dark:bg-gray-800 shadow-md rounded-lg border border-gray-200 dark:border-gray-700">
        <div cdkDragHandle class="cursor-move p-2 bg-gray-100 dark:bg-gray-700 rounded-t-lg flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>
        </div>
        
        <div class="p-2">
          <ng-container *ngIf="item === 'network'">
            <app-network-scanner></app-network-scanner>
          </ng-container>
          <ng-container *ngIf="item === 'browser'">
            <div class="p-6 text-center text-gray-500 dark:text-gray-400">Browser Module (Em breve)</div>
          </ng-container>
          <ng-container *ngIf="item === 'mail'">
            <div class="p-6 text-center text-gray-500 dark:text-gray-400">Mail Module (Em breve)</div>
          </ng-container>
        </div>
      </div>
    </div>
  `
})
export class DynamicGridComponent {
  items = ['network', 'browser', 'mail'];

  drop(event: CdkDragDrop<string[]>) {
    moveItemInArray(this.items, event.previousIndex, event.currentIndex);
  }
}
