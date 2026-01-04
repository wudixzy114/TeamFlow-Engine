// noinspection JSUnusedGlobalSymbols

declare global {
  interface LoginRequest {
    email: string;
    password: string;
  }

  interface RegisterRequest {
    username: string;
    email: string;
    password: string;
  }

  interface RefreshTokenRequest {
    refresh: string;
  }
}

export {};
