import { apiClient, tokenStorage } from "./client";
import type { TokenPair, User } from "../types/api";

export async function register(email: string, full_name: string, password: string): Promise<TokenPair> {
  const { data } = await apiClient.post<TokenPair>("/api/v1/auth/register", { email, full_name, password });
  tokenStorage.set(data);
  return data;
}

export async function login(email: string, password: string): Promise<TokenPair> {
  const { data } = await apiClient.post<TokenPair>("/api/v1/auth/login", { email, password });
  tokenStorage.set(data);
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/api/v1/auth/me");
  return data;
}

export function logout(): void {
  tokenStorage.clear();
}
