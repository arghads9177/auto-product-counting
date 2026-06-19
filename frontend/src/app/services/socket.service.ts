import { Injectable, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { environment } from '../../environments/environment';
import { CountEvent, ActivityEvent, CountSummary } from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class SocketService implements OnDestroy {
  private socket: Socket | null = null;

  readonly countEvent$ = new Subject<CountEvent>();
  readonly activityEvent$ = new Subject<ActivityEvent>();
  readonly summaryTick$ = new Subject<CountSummary>();
  readonly cameraStatus$ = new Subject<{ camera_id: string; status: string }>();
  readonly connected$ = new Subject<boolean>();

  connect() {
    if (this.socket?.connected) return;

    const url = environment.socketUrl || window.location.origin;
    this.socket = io(url, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    });

    this.socket.on('connect', () => this.connected$.next(true));
    this.socket.on('disconnect', () => this.connected$.next(false));
    this.socket.on('count_event', (data: CountEvent) => this.countEvent$.next(data));
    this.socket.on('activity_event', (data: ActivityEvent) => this.activityEvent$.next(data));
    this.socket.on('summary_tick', (data: CountSummary) => this.summaryTick$.next(data));
    this.socket.on('camera_status', (data: { camera_id: string; status: string }) =>
      this.cameraStatus$.next(data)
    );
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  ngOnDestroy() {
    this.disconnect();
  }
}
