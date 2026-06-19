import { Component, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { ApiService } from '../../services/api.service';
import { SocketService } from '../../services/socket.service';
import { Camera } from '../../models/api.models';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-cameras',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 space-y-6">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Cameras</h2>
        @if (auth.userRole() === 'ADMIN') {
          <button
            (click)="showAdd.set(!showAdd())"
            class="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition"
          >
            {{ showAdd() ? 'Cancel' : 'Add Camera' }}
          </button>
        }
      </div>

      <!-- Add Camera Form -->
      @if (showAdd()) {
        <div class="bg-white rounded-xl shadow-sm border p-5">
          <h3 class="font-semibold text-gray-900 mb-4">Add New Camera</h3>
          <form (ngSubmit)="addCamera()" class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Camera ID</label>
              <input
                [(ngModel)]="newCameraId"
                name="cameraId"
                required
                class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                placeholder="cam01"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                [(ngModel)]="newCameraName"
                name="cameraName"
                required
                class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                placeholder="Dock Bay 1"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">RTSP URL</label>
              <div class="flex gap-2">
                <input
                  [(ngModel)]="newRtspUrl"
                  name="rtspUrl"
                  required
                  class="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                  placeholder="rtsp://localhost:8554/cam01"
                />
                <button
                  type="submit"
                  [disabled]="addingCamera()"
                  class="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
                >
                  Add
                </button>
              </div>
            </div>
          </form>
        </div>
      }

      <!-- Camera Grid -->
      @if (cameras().length === 0) {
        <div class="bg-white rounded-xl shadow-sm border p-12 text-center">
          <p class="text-gray-400 text-lg">No cameras registered</p>
          <p class="text-gray-400 text-sm mt-1">Add a camera to get started</p>
        </div>
      } @else {
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          @for (cam of cameras(); track cam.camera_id) {
            <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
              <!-- Stream -->
              <div class="relative bg-black aspect-video">
                @if (cam.status === 'RUNNING') {
                  <img
                    [src]="api.getStreamUrl(cam.camera_id)"
                    [alt]="cam.name"
                    class="w-full h-full object-contain"
                    loading="lazy"
                  />
                } @else {
                  <div class="w-full h-full flex items-center justify-center text-gray-500">
                    <span class="text-sm">Camera offline</span>
                  </div>
                }
                <div class="absolute top-2 left-2">
                  <span
                    class="px-2 py-0.5 rounded text-xs font-medium"
                    [class.bg-green-500]="cam.status === 'RUNNING'"
                    [class.text-white]="cam.status === 'RUNNING'"
                    [class.bg-gray-600]="cam.status !== 'RUNNING'"
                    [class.text-gray-300]="cam.status !== 'RUNNING'"
                  >{{ cam.status }}</span>
                </div>
              </div>
              <!-- Info -->
              <div class="p-4">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="font-semibold text-gray-900">{{ cam.name }}</h3>
                    <p class="text-xs text-gray-500 mt-0.5">{{ cam.camera_id }}</p>
                  </div>
                  <div class="flex gap-2">
                    @if (cam.status !== 'RUNNING') {
                      <button
                        (click)="startCamera(cam.camera_id)"
                        class="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition"
                      >
                        Start
                      </button>
                    } @else {
                      <button
                        (click)="stopCamera(cam.camera_id)"
                        class="px-3 py-1.5 bg-red-600 text-white text-xs rounded-lg hover:bg-red-700 transition"
                      >
                        Stop
                      </button>
                    }
                  </div>
                </div>
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class CamerasComponent implements OnInit, OnDestroy {
  cameras = signal<Camera[]>([]);
  showAdd = signal(false);
  addingCamera = signal(false);
  newCameraId = '';
  newCameraName = '';
  newRtspUrl = '';

  private subs = new Subscription();

  constructor(
    public api: ApiService,
    public auth: AuthService,
    private socketService: SocketService
  ) {}

  ngOnInit() {
    this.loadCameras();
    this.subs.add(
      this.socketService.cameraStatus$.subscribe(() => this.loadCameras())
    );
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  loadCameras() {
    this.api.listCameras().subscribe(c => this.cameras.set(c));
  }

  addCamera() {
    if (!this.newCameraId || !this.newCameraName || !this.newRtspUrl) return;
    this.addingCamera.set(true);
    this.api.addCamera(this.newCameraId, this.newCameraName, this.newRtspUrl).subscribe({
      next: () => {
        this.addingCamera.set(false);
        this.showAdd.set(false);
        this.newCameraId = '';
        this.newCameraName = '';
        this.newRtspUrl = '';
        this.loadCameras();
      },
      error: () => this.addingCamera.set(false),
    });
  }

  startCamera(cameraId: string) {
    this.api.startCamera(cameraId).subscribe(() => this.loadCameras());
  }

  stopCamera(cameraId: string) {
    this.api.stopCamera(cameraId).subscribe(() => this.loadCameras());
  }
}
