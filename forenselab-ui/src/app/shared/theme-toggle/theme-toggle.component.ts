import { Component, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  template: `
    <button (click)="toggleTheme()" class="p-2 border rounded shadow hover:bg-gray-200 dark:hover:bg-gray-700">
      Toggle Theme
    </button>
  `
})
export class ThemeToggleComponent {
  isDark = false;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {}

  toggleTheme() {
    if (isPlatformBrowser(this.platformId)) {
      const html = document.documentElement;
      if (html.classList.contains('dark')) {
        html.classList.remove('dark');
        this.isDark = false;
      } else {
        html.classList.add('dark');
        this.isDark = true;
      }
    }
  }
}
