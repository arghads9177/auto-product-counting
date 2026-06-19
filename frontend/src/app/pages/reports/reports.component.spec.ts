import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ReportsComponent } from './reports.component';
import { ApiService } from '../../services/api.service';

describe('ReportsComponent', () => {
  let component: ReportsComponent;
  let fixture: ComponentFixture<ReportsComponent>;
  let apiSpy: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    apiSpy = jasmine.createSpyObj('ApiService', ['downloadReport']);

    await TestBed.configureTestingModule({
      imports: [ReportsComponent],
      providers: [{ provide: ApiService, useValue: apiSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.format).toBe('csv');
    expect(component.startDate).toBe('');
    expect(component.endDate).toBe('');
    expect(component.cameraId).toBe('');
    expect(component.downloading()).toBeFalse();
    expect(component.error()).toBe('');
  });

  // ─── Template Rendering ───────────────────────────────────────

  it('should render the Reports heading', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h2')?.textContent).toContain('Reports');
  });

  it('should render format dropdown with csv, excel, pdf options', () => {
    const el: HTMLElement = fixture.nativeElement;
    const select = el.querySelector('select') as HTMLSelectElement;
    expect(select).toBeTruthy();

    const options = select.querySelectorAll('option');
    expect(options.length).toBe(3);
    expect(options[0].value).toBe('csv');
    expect(options[1].value).toBe('excel');
    expect(options[2].value).toBe('pdf');
  });

  it('should render date inputs', () => {
    const el: HTMLElement = fixture.nativeElement;
    const dateInputs = el.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBe(2);
  });

  it('should render camera ID input with placeholder', () => {
    const el: HTMLElement = fixture.nativeElement;
    const input = el.querySelector('input[placeholder="Leave empty for all cameras"]') as HTMLInputElement;
    expect(input).toBeTruthy();
  });

  it('should render download button with correct text', () => {
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.textContent?.trim()).toContain('Download Report');
  });

  it('should not show error message initially', () => {
    const el: HTMLElement = fixture.nativeElement;
    const errorEl = el.querySelector('.text-red-600');
    expect(errorEl).toBeNull();
  });

  // ─── Happy Path: Download CSV ─────────────────────────────────

  it('should call downloadReport with csv format and no optional params', () => {
    const mockBlob = new Blob(['col1,col2\nval1,val2'], { type: 'text/csv' });
    apiSpy.downloadReport.and.returnValue(of(mockBlob));

    // Spy on DOM manipulation for blob download
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock-url');
    spyOn(URL, 'revokeObjectURL');
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        return { href: '', download: '', click: jasmine.createSpy('click') } as any;
      }
      return document.createElement(tag);
    });

    component.format = 'csv';
    component.download();

    expect(apiSpy.downloadReport).toHaveBeenCalledWith('csv', undefined, undefined, undefined);
    expect(component.downloading()).toBeFalse();
    expect(component.error()).toBe('');
  });

  it('should call downloadReport with all params when set', () => {
    apiSpy.downloadReport.and.returnValue(of(new Blob()));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(URL, 'revokeObjectURL');
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        return { href: '', download: '', click: jasmine.createSpy('click') } as any;
      }
      return document.createElement(tag);
    });

    component.format = 'pdf';
    component.startDate = '2026-01-01';
    component.endDate = '2026-01-31';
    component.cameraId = 'cam01';
    component.download();

    expect(apiSpy.downloadReport).toHaveBeenCalledWith('pdf', '2026-01-01', '2026-01-31', 'cam01');
  });

  it('should create a download link with correct file extension for csv', () => {
    apiSpy.downloadReport.and.returnValue(of(new Blob(['data'])));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(URL, 'revokeObjectURL');

    let downloadFilename = '';
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        const anchor = {
          href: '',
          download: '',
          click: jasmine.createSpy('click'),
        };
        // Capture the filename after assignment
        Object.defineProperty(anchor, 'download', {
          get() { return downloadFilename; },
          set(v) { downloadFilename = v; },
        });
        return anchor as any;
      }
      return document.createElement(tag);
    });

    component.format = 'csv';
    component.download();

    expect(downloadFilename).toBe('report.csv');
  });

  it('should use .xlsx extension for excel format', () => {
    apiSpy.downloadReport.and.returnValue(of(new Blob()));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(URL, 'revokeObjectURL');

    let downloadFilename = '';
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        const anchor = {
          href: '',
          download: '',
          click: jasmine.createSpy('click'),
        };
        Object.defineProperty(anchor, 'download', {
          get() { return downloadFilename; },
          set(v) { downloadFilename = v; },
        });
        return anchor as any;
      }
      return document.createElement(tag);
    });

    component.format = 'excel';
    component.download();

    expect(downloadFilename).toBe('report.xlsx');
  });

  it('should use .pdf extension for pdf format', () => {
    apiSpy.downloadReport.and.returnValue(of(new Blob()));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(URL, 'revokeObjectURL');

    let downloadFilename = '';
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        const anchor = {
          href: '',
          download: '',
          click: jasmine.createSpy('click'),
        };
        Object.defineProperty(anchor, 'download', {
          get() { return downloadFilename; },
          set(v) { downloadFilename = v; },
        });
        return anchor as any;
      }
      return document.createElement(tag);
    });

    component.format = 'pdf';
    component.download();

    expect(downloadFilename).toBe('report.pdf');
  });

  it('should revoke object URL after download', () => {
    apiSpy.downloadReport.and.returnValue(of(new Blob()));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:revoke-test');
    const revokeSpy = spyOn(URL, 'revokeObjectURL');
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        return { href: '', download: '', click: jasmine.createSpy('click') } as any;
      }
      return document.createElement(tag);
    });

    component.download();

    expect(revokeSpy).toHaveBeenCalledWith('blob:revoke-test');
  });

  // ─── Loading State ────────────────────────────────────────────

  it('should show "Generating..." when downloading', () => {
    component.downloading.set(true);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.textContent?.trim()).toContain('Generating...');
    expect(button.disabled).toBeTrue();
  });

  it('should disable download button while downloading', () => {
    component.downloading.set(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBeTrue();
  });

  it('should clear previous error on new download attempt', () => {
    component.error.set('Previous error');
    apiSpy.downloadReport.and.returnValue(of(new Blob()));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(URL, 'revokeObjectURL');
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        return { href: '', download: '', click: jasmine.createSpy('click') } as any;
      }
      return document.createElement(tag);
    });

    component.download();

    expect(component.error()).toBe('');
  });

  // ─── Error Handling ───────────────────────────────────────────

  it('should display error message from server on download failure', () => {
    apiSpy.downloadReport.and.returnValue(
      throwError(() => ({ error: { detail: 'No data for date range' } }))
    );

    component.download();
    fixture.detectChanges();

    expect(component.downloading()).toBeFalse();
    expect(component.error()).toBe('No data for date range');

    const el: HTMLElement = fixture.nativeElement;
    const errorEl = el.querySelector('.text-red-600');
    expect(errorEl?.textContent?.trim()).toBe('No data for date range');
  });

  it('should display generic error when no detail in response', () => {
    apiSpy.downloadReport.and.returnValue(
      throwError(() => ({ error: {} }))
    );

    component.download();

    expect(component.error()).toBe('Failed to generate report');
  });

  it('should display generic error for network errors', () => {
    apiSpy.downloadReport.and.returnValue(
      throwError(() => ({ error: null }))
    );

    component.download();

    expect(component.error()).toBe('Failed to generate report');
    expect(component.downloading()).toBeFalse();
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should pass undefined for empty optional fields', () => {
    apiSpy.downloadReport.and.returnValue(of(new Blob()));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(URL, 'revokeObjectURL');
    spyOn(document, 'createElement').and.callFake((tag: string) => {
      if (tag === 'a') {
        return { href: '', download: '', click: jasmine.createSpy('click') } as any;
      }
      return document.createElement(tag);
    });

    component.startDate = '';
    component.endDate = '';
    component.cameraId = '';
    component.download();

    expect(apiSpy.downloadReport).toHaveBeenCalledWith('csv', undefined, undefined, undefined);
  });

  // ─── Form Labels (Accessibility) ─────────────────────────────

  it('should have visible labels for all form fields', () => {
    const el: HTMLElement = fixture.nativeElement;
    const labels = el.querySelectorAll('label');
    expect(labels.length).toBeGreaterThanOrEqual(4); // Format, Start Date, End Date, Camera ID
  });
});
