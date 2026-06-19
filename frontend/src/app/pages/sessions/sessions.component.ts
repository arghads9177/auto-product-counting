import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Session } from '../../models/api.models';

@Component({
  selector: 'app-sessions',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 space-y-6">
      <h2 class="text-2xl font-bold text-gray-900">Sessions</h2>

      <!-- Filters -->
      <div class="bg-white rounded-xl shadow-sm border p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Status</label>
          <select
            [(ngModel)]="filterStatus"
            (ngModelChange)="loadSessions()"
            class="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          >
            <option value="">All</option>
            <option value="ACTIVE">Active</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Camera ID</label>
          <input
            [(ngModel)]="filterCamera"
            (ngModelChange)="loadSessions()"
            placeholder="e.g. cam01"
            class="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          />
        </div>
      </div>

      <!-- Sessions Table -->
      <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr class="text-left text-gray-500">
                <th class="px-5 py-3 font-medium">Session ID</th>
                <th class="px-5 py-3 font-medium">Camera</th>
                <th class="px-5 py-3 font-medium">Status</th>
                <th class="px-5 py-3 font-medium">Direction</th>
                <th class="px-5 py-3 font-medium">Loading</th>
                <th class="px-5 py-3 font-medium">Unloading</th>
                <th class="px-5 py-3 font-medium">Started</th>
                <th class="px-5 py-3 font-medium">Ended</th>
              </tr>
            </thead>
            <tbody>
              @if (sessions().length === 0) {
                <tr>
                  <td colspan="8" class="px-5 py-8 text-center text-gray-400">No sessions found</td>
                </tr>
              }
              @for (s of sessions(); track s.session_id) {
                <tr class="border-t hover:bg-gray-50 cursor-pointer" (click)="selectSession(s)">
                  <td class="px-5 py-3 font-mono text-xs">{{ s.session_id | slice:0:12 }}...</td>
                  <td class="px-5 py-3 font-medium">{{ s.camera_id }}</td>
                  <td class="px-5 py-3">
                    <span
                      class="px-2 py-0.5 rounded text-xs font-medium"
                      [class.bg-green-100]="s.status === 'ACTIVE'"
                      [class.text-green-700]="s.status === 'ACTIVE'"
                      [class.bg-gray-100]="s.status === 'COMPLETED'"
                      [class.text-gray-700]="s.status === 'COMPLETED'"
                      [class.bg-yellow-100]="s.status !== 'ACTIVE' && s.status !== 'COMPLETED'"
                      [class.text-yellow-700]="s.status !== 'ACTIVE' && s.status !== 'COMPLETED'"
                    >{{ s.status }}</span>
                  </td>
                  <td class="px-5 py-3">{{ s.direction ?? '-' }}</td>
                  <td class="px-5 py-3">{{ s.loading_count ?? 0 }}</td>
                  <td class="px-5 py-3">{{ s.unloading_count ?? 0 }}</td>
                  <td class="px-5 py-3 text-gray-500">{{ s.started_at | date:'short' }}</td>
                  <td class="px-5 py-3 text-gray-500">{{ s.ended_at ? (s.ended_at | date:'short') : '-' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- Session Detail Modal -->
      @if (selectedSession()) {
        <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" (click)="selectedSession.set(null)">
          <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-y-auto m-4" (click)="$event.stopPropagation()">
            <div class="p-5 border-b flex items-center justify-between">
              <h3 class="font-semibold text-gray-900">Session Details</h3>
              <button (click)="selectedSession.set(null)" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div class="p-5 space-y-4">
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-500">Session ID:</span>
                  <span class="ml-2 font-mono text-xs">{{ selectedSession()!.session_id }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Camera:</span>
                  <span class="ml-2 font-medium">{{ selectedSession()!.camera_id }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Status:</span>
                  <span class="ml-2">{{ selectedSession()!.status }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Direction:</span>
                  <span class="ml-2">{{ selectedSession()!.direction ?? '-' }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Loading:</span>
                  <span class="ml-2 font-bold text-primary-600">{{ selectedSession()!.loading_count ?? 0 }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Unloading:</span>
                  <span class="ml-2 font-bold text-orange-500">{{ selectedSession()!.unloading_count ?? 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class SessionsComponent implements OnInit {
  sessions = signal<Session[]>([]);
  selectedSession = signal<Session | null>(null);
  filterStatus = '';
  filterCamera = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadSessions();
  }

  loadSessions() {
    this.api
      .getSessions(this.filterStatus || undefined, this.filterCamera || undefined)
      .subscribe(s => this.sessions.set(s));
  }

  selectSession(session: Session) {
    this.selectedSession.set(session);
  }
}
