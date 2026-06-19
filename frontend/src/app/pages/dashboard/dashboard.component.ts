import { Component, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, interval, startWith, switchMap } from 'rxjs';
import { ApiService } from '../../services/api.service';
import { SocketService } from '../../services/socket.service';
import { CountSummary, Session, ActivityEvent } from '../../models/api.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Dashboard</h2>
        <div class="flex items-center gap-2">
          <span
            class="w-2.5 h-2.5 rounded-full"
            [class.bg-green-500]="socketConnected()"
            [class.bg-red-500]="!socketConnected()"
          ></span>
          <span class="text-sm text-gray-500">{{ socketConnected() ? 'Live' : 'Disconnected' }}</span>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl shadow-sm border p-5">
          <p class="text-sm text-gray-500">Total Loading</p>
          <p class="text-3xl font-bold text-primary-600 mt-1">{{ summary()?.total_loading ?? 0 }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border p-5">
          <p class="text-sm text-gray-500">Total Unloading</p>
          <p class="text-3xl font-bold text-orange-500 mt-1">{{ summary()?.total_unloading ?? 0 }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border p-5">
          <p class="text-sm text-gray-500">Active Cameras</p>
          <p class="text-3xl font-bold text-green-600 mt-1">{{ summary()?.active_cameras ?? 0 }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border p-5">
          <p class="text-sm text-gray-500">Active Sessions</p>
          <p class="text-3xl font-bold text-purple-600 mt-1">{{ summary()?.active_sessions ?? 0 }}</p>
        </div>
      </div>

      <!-- Active Sessions -->
      <div class="bg-white rounded-xl shadow-sm border">
        <div class="px-5 py-4 border-b">
          <h3 class="font-semibold text-gray-900">Active Sessions</h3>
        </div>
        <div class="p-5">
          @if ((summary()?.active_sessions_detail?.length ?? 0) === 0) {
            <p class="text-gray-400 text-sm">No active sessions</p>
          } @else {
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-gray-500 border-b">
                    <th class="pb-2 font-medium">Camera</th>
                    <th class="pb-2 font-medium">Direction</th>
                    <th class="pb-2 font-medium">Loading</th>
                    <th class="pb-2 font-medium">Unloading</th>
                    <th class="pb-2 font-medium">Started</th>
                  </tr>
                </thead>
                <tbody>
                  @for (s of summary()?.active_sessions_detail ?? []; track s.session_id) {
                    <tr class="border-b last:border-0">
                      <td class="py-2.5 font-medium text-gray-900">{{ s.camera_id }}</td>
                      <td class="py-2.5">
                        <span
                          class="px-2 py-0.5 rounded text-xs font-medium"
                          [class.bg-blue-100]="s.direction === 'loading'"
                          [class.text-blue-700]="s.direction === 'loading'"
                          [class.bg-orange-100]="s.direction === 'unloading'"
                          [class.text-orange-700]="s.direction === 'unloading'"
                          [class.bg-gray-100]="s.direction !== 'loading' && s.direction !== 'unloading'"
                          [class.text-gray-700]="s.direction !== 'loading' && s.direction !== 'unloading'"
                        >{{ s.direction ?? 'detecting' }}</span>
                      </td>
                      <td class="py-2.5">{{ s.loading_count ?? 0 }}</td>
                      <td class="py-2.5">{{ s.unloading_count ?? 0 }}</td>
                      <td class="py-2.5 text-gray-500">{{ s.started_at | date:'short' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="bg-white rounded-xl shadow-sm border">
        <div class="px-5 py-4 border-b">
          <h3 class="font-semibold text-gray-900">Recent Activity</h3>
        </div>
        <div class="p-5 space-y-3 max-h-80 overflow-y-auto">
          @if (events().length === 0) {
            <p class="text-gray-400 text-sm">No recent events</p>
          }
          @for (e of events(); track $index) {
            <div class="flex items-start gap-3 text-sm">
              <span class="mt-0.5 w-2 h-2 rounded-full flex-shrink-0"
                [class.bg-blue-500]="e.event_type === 'SESSION_START'"
                [class.bg-red-500]="e.event_type === 'SESSION_END'"
                [class.bg-green-500]="e.event_type !== 'SESSION_START' && e.event_type !== 'SESSION_END'"
              ></span>
              <div>
                <span class="font-medium text-gray-900">{{ e.event_type }}</span>
                <span class="text-gray-500 ml-2">{{ e.camera_id }}</span>
                <span class="text-gray-400 ml-2 text-xs">{{ e.timestamp | date:'short' }}</span>
              </div>
            </div>
          }
        </div>
      </div>
    </div>
  `,
})
export class DashboardComponent implements OnInit, OnDestroy {
  summary = signal<CountSummary | null>(null);
  events = signal<ActivityEvent[]>([]);
  socketConnected = signal(false);

  private subs = new Subscription();

  constructor(
    private api: ApiService,
    private socketService: SocketService
  ) {}

  ngOnInit() {
    this.socketService.connect();

    this.subs.add(
      interval(5000)
        .pipe(startWith(0), switchMap(() => this.api.getCountsSummary()))
        .subscribe(s => this.summary.set(s))
    );

    this.subs.add(
      this.api.getEventTimeline(20).subscribe(e => this.events.set(e))
    );

    this.subs.add(
      this.socketService.summaryTick$.subscribe(s => this.summary.set(s))
    );

    this.subs.add(
      this.socketService.connected$.subscribe(c => this.socketConnected.set(c))
    );

    this.subs.add(
      this.socketService.activityEvent$.subscribe(e => {
        this.events.update(prev => [e, ...prev].slice(0, 20));
      })
    );
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }
}
