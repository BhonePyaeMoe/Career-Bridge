import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export type User = { id: number; username: string; role: 'student' | 'company' | 'admin' };
export type Choice = { value: string; label: string };
export type Skill = { id: number; name: string };
export type Options = { skills: Skill[]; job_types: Choice[]; work_modes: Choice[]; universities: Choice[] };
export type Row = Record<string, any>;
export type Listing = { count: number; next: string | null; previous: string | null; results: Row[] };
const defaultAvatar = '/assets/default-avatar.png';

@Injectable({providedIn: 'root'})
export class Api {
  private http = inject(HttpClient);
  readonly user = signal<User | null>(null);
  private readonly avatar = signal(defaultAvatar);
  readonly avatarSrc = this.avatar.asReadonly();
  private avatarRequest = 0;
  private optionsRequest?: Promise<Options>;
  get<T>(path: string, query: Record<string, string> = {}): Promise<T> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) if (value.trim()) params = params.set(key, value);
    return firstValueFrom(this.http.get<T>(`/api/${path}`, {params}));
  }
  options() {
    return this.optionsRequest ??= this.get<Options>('options/').catch(error => {
      this.optionsRequest = undefined;
      throw error;
    });
  }
  async session() {
    const value = await this.get<{user: User | null}>('auth/session/');
    this.avatar.set(defaultAvatar);
    this.user.set(value.user);
    void this.refreshAvatar();
  }
  async refreshAvatar() {
    const request = ++this.avatarRequest;
    const user = this.user();
    if (!user || user.role === 'admin') {
      this.avatar.set(defaultAvatar);
      return;
    }
    try {
      const result = await this.get<{profile: {profile_picture_url?: string | null} | null}>(`${user.role}/profile/`);
      if (this.user() === user && request === this.avatarRequest) {
        this.avatar.set(result.profile?.profile_picture_url || defaultAvatar);
      }
    } catch {
      if (this.user() === user && request === this.avatarRequest) this.avatar.set(defaultAvatar);
    }
  }
  useDefaultAvatar() {
    this.avatar.set(defaultAvatar);
  }
  async post(path: string, form = new FormData()) {
    await this.get('auth/csrf/');
    return firstValueFrom(this.http.post<{id?: number}>(`/api/${path}`, form));
  }
}

export function errorMessages(error: unknown): string[] {
  if (error instanceof HttpErrorResponse) {
    const errors = error.error?.errors as Record<string, string[]> | undefined;
    if (errors) return Object.entries(errors).flatMap(([key, values]) =>
      values.map(value => key === '__all__' ? value : `${label(key)}: ${value}`));
    if (typeof error.error?.detail === 'string') return [error.error.detail];
    if (error.status === 403) return ['This request was denied. Sign in with the correct account and try again.'];
    if (error.status === 404) return ['This record is unavailable. It may be private or no longer open.'];
  }
  return ['Could not complete the request. Check that Django is running and try again.'];
}

export function label(value: string | null | undefined) {
  return (value || '').replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase());
}
