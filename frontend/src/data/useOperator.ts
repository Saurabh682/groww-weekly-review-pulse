import { useEffect, useState } from 'react';
import { Session, SupabaseClient } from '@supabase/supabase-js';
import { ApiError, sendJson } from './apiClient';
import { operatorClient } from './operatorClient';
import { Operator, OperatorSession } from './types';

const MANAGE_PATH = '/manage';
const NOT_AN_ACCOUNT = ['otp_disabled', 'signup_disabled', 'user_not_found'];
const LINK_MARKS = ['code', 'error', 'error_code'];

function cameFromLink(): boolean {
  const query = new URLSearchParams(window.location.search);
  const hash = new URLSearchParams(window.location.hash.slice(1));
  return LINK_MARKS.some((mark) => query.has(mark) || hash.has(mark));
}

function toOperatorSession(session: Session | null): OperatorSession {
  return session
    ? { status: 'signed_in', email: session.user.email ?? 'Signed in' }
    : { status: 'signed_out', linkFailed: cameFromLink() };
}

function required(client: SupabaseClient | null): SupabaseClient {
  if (!client) throw new Error('Sign-in is not set up for this dashboard.');
  return client;
}

async function requestLink(email: string): Promise<void> {
  const { error } = await required(operatorClient()).auth.signInWithOtp({
    email,
    options: { shouldCreateUser: false, emailRedirectTo: `${window.location.origin}${MANAGE_PATH}` },
  });
  if (error && !NOT_AN_ACCOUNT.includes(error.code ?? '')) {
    throw new Error(`The sign-in link could not be sent: ${error.message}`);
  }
}

async function signOut(): Promise<void> {
  const { error } = await required(operatorClient()).auth.signOut({ scope: 'local' });
  if (error) throw error;
}

const send: Operator['send'] = async (method, path, body) => {
  const { data } = await required(operatorClient()).auth.getSession();
  if (!data.session) throw new ApiError('Your session has ended. Sign in again.', null);
  return sendJson(method, path, body, data.session.access_token);
};

export function useOperator(): Operator {
  const client = operatorClient();
  const [session, setSession] = useState<OperatorSession>({ status: client ? 'checking' : 'unavailable' });

  useEffect(() => {
    if (!client) return undefined;
    const { data } = client.auth.onAuthStateChange((_event, next) => setSession(toOperatorSession(next)));
    return () => data.subscription.unsubscribe();
  }, [client]);

  return { session, requestLink, signOut, send };
}
