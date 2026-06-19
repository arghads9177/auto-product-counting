import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { SystemLog } from '../../models/api.models';

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 space-y-6">
      <h2 class="text-2xl font-bold text-gray-900">System Logs</h2>

      <!-- Filters -->
      <div class="bg-white rounded-xl shadow-sm border p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Severity</label>
          <select
            [(ngModel)]="filterSeverity"
            (ngModelChange)="loadLogs()"
            class="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          >
            <option value="">All</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Category</label>
          <select
            [(ngModel)]="filterCategory"
            (ngModelChange)="loadLogs()"
            class="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          >
            <option value="">All</option>
            <option value="SYSTEM">System</option>
            <option value="DETECTION">Detection</option>
            <option value="TRACKING">Tracking</option>
            <option value="SESSION">Session</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Camera ID</label>
          <input
            [(ngModel)]="filterCamera"
            (ngModelChange)="loadLogs()"
            placeholder="e.g. cam01"
            class="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          />
        </div>
      </div>

      <!-- Logs Table -->
      <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr class="text-left text-gray-500">
                <th class="px-5 py-3 font-medium">Time</th>
                <th class="px-5 py-3 font-medium">Severity</th>
                <th class="px-5 py-3 font-medium">Category</th>
                <th class="px-5 py-3 font-medium">Camera</th>
                <th class="px-5 py-3 font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              @if (logs().length === 0) {
                <tr>
                  <td colspan="5" class="px-5 py-8 text-center text-gray-400">No logs found</td>
                </tr>
              }
              @for (log of logs(); track $index) {
                <tr class="border-t hover:bg-gray-50">
                  <td class="px-5 py-3 text-gray-500 whitespace-nowrap">{{ log.timestamp | date:'medium' }}</td>
                  <td class="px-5 py-3">
                    <span
                      class="px-2 py-0.5 rounded text-xs font-medium"
                      [class.bg-blue-100]="log.severity === 'INFO'"
                      [class.text-blue-700]="log.severity === 'INFO'"
                      [class.bg-yellow-100]="log.severity === 'WARNING'"
                      [class.text-yellow-700]="log.severity === 'WARNING'"
                      [class.bg-red-100]="log.severity === 'ERROR'"
                      [class.text-red-700]="log.severity === 'ERROR'"
                    >{{ log.severity }}</span>
                  </td>
                  <td class="px-5 py-3 text-gray-700">{{ log.category }}</td>
                  <td class="px-5 py-3 text-gray-700">{{ log.camera_id ?? '-' }}</td>
                  <td class="px-5 py-3 text-gray-900">{{ log.message }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
})
export class LogsComponent implements OnInit {
  logs = signal<SystemLog[]>([]);
  filterSeverity = '';
  filterCategory = '';
  filterCamera = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    this.api
      .getLogs(
        100,
        this.filterCategory || undefined,
        this.filterSeverity || undefined,
        this.filterCamera || undefined
      )
      .subscribe(l => this.logs.set(l));
  }
}
