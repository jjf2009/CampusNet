"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchEvents,
  fetchOverview,
  fetchStats,
  fetchUsers,
  type AuthEvent,
  type Result,
  type Stats,
  type SystemOverview,
  type UserActivity,
} from "./api";

const POLL_MS = 7000;

export interface DashboardState {
  stats: Stats | null;
  overview: SystemOverview | null;
  events: AuthEvent[];
  users: UserActivity[];
  username: string;
  result: Result | "";
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  setUsername: (value: string) => void;
  setResult: (value: Result | "") => void;
  refresh: () => void;
}

export function useDashboard(): DashboardState {
  const [stats, setStats] = useState<Stats | null>(null);
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [events, setEvents] = useState<AuthEvent[]>([]);
  const [users, setUsers] = useState<UserActivity[]>([]);
  const [username, setUsername] = useState("");
  const [result, setResult] = useState<Result | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Keep latest filter values available to the interval without resetting it.
  const filtersRef = useRef({ username, result });
  filtersRef.current = { username, result };

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const { username: u, result: r } = filtersRef.current;
      const [s, o, e, usr] = await Promise.all([
        fetchStats(signal),
        fetchOverview(signal),
        fetchEvents({ username: u, result: r, limit: 50 }, signal),
        fetchUsers(signal),
      ]);
      setStats(s);
      setOverview(o);
      setEvents(e.items);
      setUsers(usr);
      setError(null);
      setLastUpdated(new Date());
    } catch (cause) {
      if ((cause as Error)?.name === "AbortError") return;
      setError(cause instanceof Error ? cause.message : "Backend unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  // Refetch when filters change (debounced) and poll on an interval.
  useEffect(() => {
    const controller = new AbortController();
    const debounce = setTimeout(() => void load(controller.signal), 250);
    return () => {
      clearTimeout(debounce);
      controller.abort();
    };
  }, [username, result, load]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setInterval(() => void load(controller.signal), POLL_MS);
    return () => {
      clearInterval(timer);
      controller.abort();
    };
  }, [load]);

  const refresh = useCallback(() => void load(), [load]);

  return {
    stats,
    overview,
    events,
    users,
    username,
    result,
    loading,
    error,
    lastUpdated,
    setUsername,
    setResult,
    refresh,
  };
}
