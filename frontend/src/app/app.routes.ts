import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { LayoutComponent } from './components/layout/layout.component';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component').then(m => m.LoginComponent),
  },
  {
    path: '',
    component: LayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
      },
      {
        path: 'cameras',
        loadComponent: () =>
          import('./pages/cameras/cameras.component').then(m => m.CamerasComponent),
      },
      {
        path: 'sessions',
        loadComponent: () =>
          import('./pages/sessions/sessions.component').then(m => m.SessionsComponent),
      },
      {
        path: 'reports',
        loadComponent: () =>
          import('./pages/reports/reports.component').then(m => m.ReportsComponent),
      },
      {
        path: 'logs',
        loadComponent: () =>
          import('./pages/logs/logs.component').then(m => m.LogsComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
