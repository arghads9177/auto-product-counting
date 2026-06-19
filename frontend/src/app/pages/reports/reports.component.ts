import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 space-y-6">
      <h2 class="text-2xl font-bold text-gray-900">Reports</h2>

      <div class="bg-white rounded-xl shadow-sm border p-6 max-w-xl">
        <h3 class="font-semibold text-gray-900 mb-4">Generate Report</h3>
        <form (ngSubmit)="download()" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
            <select
              [(ngModel)]="format"
              name="format"
              class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="csv">CSV</option>
              <option value="excel">Excel</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                [(ngModel)]="startDate"
                name="startDate"
                class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                [(ngModel)]="endDate"
                name="endDate"
                class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Camera ID (optional)</label>
            <input
              [(ngModel)]="cameraId"
              name="cameraId"
              placeholder="Leave empty for all cameras"
              class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <button
            type="submit"
            [disabled]="downloading()"
            class="px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition"
          >
            {{ downloading() ? 'Generating...' : 'Download Report' }}
          </button>
          @if (error()) {
            <p class="text-red-600 text-sm">{{ error() }}</p>
          }
        </form>
      </div>
    </div>
  `,
})
export class ReportsComponent {
  format = 'csv';
  startDate = '';
  endDate = '';
  cameraId = '';
  downloading = signal(false);
  error = signal('');

  constructor(private api: ApiService) {}

  download() {
    this.downloading.set(true);
    this.error.set('');
    this.api
      .downloadReport(
        this.format,
        this.startDate || undefined,
        this.endDate || undefined,
        this.cameraId || undefined
      )
      .subscribe({
        next: (blob) => {
          this.downloading.set(false);
          const ext = this.format === 'excel' ? 'xlsx' : this.format;
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `report.${ext}`;
          a.click();
          URL.revokeObjectURL(url);
        },
        error: (err) => {
          this.downloading.set(false);
          this.error.set(err.error?.detail || 'Failed to generate report');
        },
      });
  }
}
