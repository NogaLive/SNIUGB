import { Injectable, signal, computed } from '@angular/core';

export type UserRole = 'ganadero' | 'admin';

const ACCESS_KEYS = ['access_token', 'sniugb_auth_token'];
const ROLE_KEYS   = ['role', 'sniugb_user_role'];

function readFirst(keys: string[]): string | null {
  for (const k of keys) {
    const v = localStorage.getItem(k);
    if (v) return v;
  }
  return null;
}
function writeAll(keys: string[], value: string) {
  keys.forEach(k => localStorage.setItem(k, value));
}
function removeAll(keys: string[]) {
  keys.forEach(k => localStorage.removeItem(k));
}

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private _access = signal<string | null>(readFirst(ACCESS_KEYS));
  private _role   = signal<UserRole | null>(readFirst(ROLE_KEYS) as UserRole | null);

  accessToken = this._access.asReadonly();
  role        = this._role.asReadonly();
  isLoggedIn  = computed(() => !!this._access());

  setSession(token: string, role: UserRole) {
    this._access.set(token);
    this._role.set(role);
    writeAll(ACCESS_KEYS, token);
    writeAll(ROLE_KEYS,   role);
  }

  clear() {
    this._access.set(null);
    this._role.set(null);
    removeAll(ACCESS_KEYS);
    removeAll(ROLE_KEYS);
  }
}