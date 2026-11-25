import { useCallback, useEffect, useState } from 'react';
import { ApiError, getJson, messageOf } from './apiClient';
import { ApiResource, ApiState } from './types';

interface Held<T> {
  path: string;
  state: ApiState<T>;
}

const NOT_FOUND = 404;

export const REFRESH_MS = 60_000;

interface UseApiOptions<T> {
  slowMeansWaking?: boolean;
  refreshWhile?: (data: T) => boolean;
}

interface Attempt {
  quiet: boolean;
}

const VISIBLE = 'visible';

function isReady<T>(held: Held<T>, path: string): boolean {
  return held.path === path && held.state.status === 'ready';
}

function failure<T>(error: unknown): ApiState<T> {
  const missing = error instanceof ApiError && error.status === NOT_FOUND;
  return { status: missing ? 'missing' : 'error', message: messageOf(error) };
}

export function useApi<T>(
  path: string,
  { slowMeansWaking = false, refreshWhile }: UseApiOptions<T> = {},
): ApiResource<T> {
  const [held, setHeld] = useState<Held<T>>({ path, state: { status: 'loading' } });
  const [attempt, setAttempt] = useState<Attempt>({ quiet: false });

  useEffect(() => {
    const controller = new AbortController();
    const hold = (state: ApiState<T>) => {
      const quietFailure = attempt.quiet && (state.status === 'error' || state.status === 'waking');
      if (!controller.signal.aborted) {
        setHeld((shown) => (quietFailure && isReady(shown, path) ? shown : { path, state }));
      }
    };
    setHeld((shown) => (isReady(shown, path) ? shown : { path, state: { status: 'loading' } }));
    getJson<T>(path, { signal: controller.signal, onWaking: () => hold({ status: 'waking' }), slowMeansWaking }).then(
      (data) => hold({ status: 'ready', data }),
      (error) => hold(failure(error)),
    );
    return () => controller.abort();
  }, [path, attempt, slowMeansWaking]);

  const state: ApiState<T> = held.path === path ? held.state : { status: 'loading' };
  const ready = state.status === 'ready';
  const waiting = state.status === 'ready' && refreshWhile !== undefined && refreshWhile(state.data);

  useEffect(() => {
    if (!ready) return undefined;
    const refresh = () => {
      if (document.visibilityState === VISIBLE) setAttempt({ quiet: true });
    };
    document.addEventListener('visibilitychange', refresh);
    const timer = waiting ? setInterval(refresh, REFRESH_MS) : undefined;
    return () => {
      document.removeEventListener('visibilitychange', refresh);
      clearInterval(timer);
    };
  }, [path, ready, waiting]);

  const retry = useCallback(() => setAttempt({ quiet: false }), []);
  return { state, retry };
}
