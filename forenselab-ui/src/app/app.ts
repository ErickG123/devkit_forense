import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeToggleComponent } from './shared/theme-toggle/theme-toggle.component';
import { NetworkScannerComponent } from './features/network/components/network-scanner/network-scanner.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ThemeToggleComponent, NetworkScannerComponent],
  templateUrl: './app.html'
})
export class App {
  title = 'forenselab-ui';
}
