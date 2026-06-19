import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="flex h-screen bg-gray-100">
      <aside class="w-64 bg-gray-900 text-white flex flex-col">
        <div class="p-4 border-b border-gray-700">
          <h1 class="text-lg font-bold tracking-tight">Product Counter</h1>
          <p class="text-xs text-gray-400 mt-1">Warehouse Monitoring</p>
        </div>
        <nav class="flex-1 p-3 space-y-1">
          @for (item of navItems; track item.path) {
            <a
              [routerLink]="item.path"
              routerLinkActive="bg-primary-700 text-white"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
            >
              <span class="text-lg">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </a>
          }
        </nav>
        <div class="p-4 border-t border-gray-700">
          <div class="text-sm text-gray-400">
            {{ auth.user()?.username }}
            <span class="ml-1 text-xs px-1.5 py-0.5 rounded bg-gray-700">{{ auth.user()?.role }}</span>
          </div>
          <button
            (click)="auth.logout()"
            class="mt-2 text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main class="flex-1 overflow-auto">
        <router-outlet />
      </main>
    </div>
  `,
})
export class LayoutComponent {
  constructor(public auth: AuthService) {}

  navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '\u{1F4CA}' },
    { path: '/cameras', label: 'Cameras', icon: '\u{1F4F9}' },
    { path: '/sessions', label: 'Sessions', icon: '\u{1F4C1}' },
    { path: '/reports', label: 'Reports', icon: '\u{1F4C4}' },
    { path: '/logs', label: 'System Logs', icon: '\u{1F4DD}' },
  ];
}
