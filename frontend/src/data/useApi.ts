import { useCallback, useEffect, useState } from 'react';
import { ApiError, getJson } from './apiClient';
import { ApiResource, ApiState } from './types';

interface Held<T> {
  path: string;
  state: ApiState<T>;
}

const NOT_FOUND = 404;

interface UseApiOptions {
  slowMeansWaking: boolean;
}

const AWAKE: UseApiOptions = { slowMeansWaking: false };

function failure<T>(error: unknown): ApiState<T> {
  const message = error instanceof Error ? error.message : 'The data could not be read.';
  const missing = error instanceof ApiError && error.status === NOT_FOUND;
  return { status: missing ? 'missing' : 'error', message };
}

export function useApi<T>(path: string, { slowMeansWaking } = AWAKE): ApiResource<T> {
  const [held, setHeld] = useState<Held<T>>({ path, state: { status: 'loading' } });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const hold = (state: ApiState<T>) => {
      if (!controller.signal.aborted) setHeld({ path, state });
    };
    hold({ status: 'loading' });
    getJson<T>(path, { signal: controller.signal, onWaking: () => hold({ status: 'waking' }), slowMeansWaking }).then(
      (data) => hold({ status: 'ready', data }),
      (error) => hold(failure(error)),
    );
    return () => controller.abort();
  }, [path, attempt, slowMeansWaking]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  const state: ApiState<T> = held.path === path ? held.state : { status: 'loading' };
  return { state, retry };
}
