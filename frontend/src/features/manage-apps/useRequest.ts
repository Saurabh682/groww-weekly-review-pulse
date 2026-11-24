import { useState } from 'react';
import { messageOf } from '../../data/apiClient';

export interface RequestState {
  busy: boolean;
  problem: string | null;
  run: <T>(request: () => Promise<T>, onDone: (result: T) => void) => Promise<void>;
}

export function useRequest(): RequestState {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const run: RequestState['run'] = async (request, onDone) => {
    setBusy(true);
    setProblem(null);
    try {
      onDone(await request());
    } catch (error) {
      setProblem(messageOf(error));
    } finally {
      setBusy(false);
    }
  };

  return { busy, problem, run };
}
