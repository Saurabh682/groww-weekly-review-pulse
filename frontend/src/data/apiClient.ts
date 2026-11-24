export const SLOW_RESPONSE_MS = 4_000;
export const RETRY_DELAY_MS = 3_000;
export const WAKE_LIMIT_MS = 120_000;
const ASLEEP_STATUSES = [502, 503, 504];

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
  ) {
    super(message);
  }
}

interface RequestOptions {
  signal: AbortSignal;
  onWaking: () => void;
  slowMeansWaking: boolean;
}

function apiUrl(path: string): string {
  const base = import.meta.env.VITE_API_URL;
  if (!base) {
    throw new ApiError('This dashboard has no data address. Set VITE_API_URL and build it again.', null);
  }
  return `${base.replace(/\/$/, '')}${path}`;
}

function pause(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const stop = () => {
      clearTimeout(timer);
      reject(signal.reason);
    };
    const timer = setTimeout(() => {
      signal.removeEventListener('abort', stop);
      resolve();
    }, ms);
    signal.addEventListener('abort', stop, { once: true });
  });
}

async function answerOrAsleep(url: string, signal: AbortSignal): Promise<Response | 'asleep'> {
  try {
    const response = await fetch(url, { signal });
    return ASLEEP_STATUSES.includes(response.status) ? 'asleep' : response;
  } catch (error) {
    if (signal.aborted) throw error;
    return 'asleep';
  }
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new ApiError(`The data service sent an unexpected answer (status ${response.status}).`, response.status);
  }
  const body = await response.json();
  if (!response.ok) {
    throw new ApiError(body.error ?? `The data service answered with status ${response.status}.`, response.status);
  }
  return body;
}

export async function getJson<T>(path: string, { signal, onWaking, slowMeansWaking }: RequestOptions): Promise<T> {
  const url = apiUrl(path);
  const slowTimer = slowMeansWaking ? setTimeout(onWaking, SLOW_RESPONSE_MS) : undefined;
  const deadline = Date.now() + WAKE_LIMIT_MS;
  try {
    let answer = await answerOrAsleep(url, signal);
    while (answer === 'asleep') {
      onWaking();
      if (Date.now() >= deadline) {
        throw new ApiError('The data service did not wake up. Try again in a minute.', null);
      }
      await pause(RETRY_DELAY_MS, signal);
      answer = await answerOrAsleep(url, signal);
    }
    return await readJson<T>(answer);
  } finally {
    clearTimeout(slowTimer);
  }
}
