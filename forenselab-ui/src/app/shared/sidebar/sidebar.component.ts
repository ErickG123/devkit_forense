import { Component } from '@angular/core';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  template: `
    <aside class="w-64 h-full bg-gray-100 dark:bg-gray-800 shadow-md">
      <nav class="p-4 space-y-2">
        <a href="#" class="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700">Network</a>
        <a href="#" class="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700">Browser</a>
        <a href="#" class="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700">Mail</a>
      </nav>
    </aside>
  `,
  styles: []
})
export class SidebarComponent {}
