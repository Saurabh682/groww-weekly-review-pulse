import React, { useState } from 'react';
import { LogOut, Mail } from 'lucide-react';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { ErrorState } from '../../components/ErrorState';
import { Operator } from '../../data/types';
import { TextField } from './TextField';
import { useRequest } from './useRequest';

const TEXT = 'text-xs text-text-secondary leading-relaxed break-words';

interface SignInCardProps {
  operator: Operator;
}

const LinkForm: React.FC<SignInCardProps> = ({ operator }) => {
  const [email, setEmail] = useState('');
  const [requested, setRequested] = useState(false);
  const request = useRequest();

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setRequested(false);
    request.run(() => operator.requestLink(email.trim()), () => setRequested(true));
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className={TEXT}>Anyone can read this page. Sign in as an operator to change it.</p>
      <TextField label="Email" type="email" autoComplete="email" value={email} onChange={setEmail} required />
      <Button
        type="submit"
        size="sm"
        icon={<Mail className="w-3.5 h-3.5" />}
        loading={request.busy}
        disabled={!email.trim()}
      >
        Email me a sign-in link
      </Button>
      {requested && (
        <p role="status" aria-label="Sign-in link" className={TEXT}>
          If this address belongs to an operator, a sign-in link is on its way. Open it in this browser.
        </p>
      )}
      {request.problem && <ErrorState headingLevel={3} title="No link sent" message={request.problem} />}
    </form>
  );
};

const SignOut: React.FC<SignInCardProps & { email: string }> = ({ operator, email }) => {
  const request = useRequest();
  return (
    <div className="space-y-4">
      <p className={TEXT}>
        Signed in as <span className="font-mono text-text-primary break-all">{email}</span>
      </p>
      <Button
        variant="secondary"
        size="sm"
        icon={<LogOut className="w-3.5 h-3.5" />}
        loading={request.busy}
        onClick={() => request.run(operator.signOut, () => undefined)}
      >
        Sign out
      </Button>
      {request.problem && <ErrorState headingLevel={3} title="Not signed out" message={request.problem} />}
    </div>
  );
};

const SessionPanel: React.FC<SignInCardProps> = ({ operator }) => {
  const { session } = operator;
  switch (session.status) {
    case 'unavailable':
      return (
        <p className={TEXT}>
          Sign-in is not set up for this dashboard. Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY and build it
          again.
        </p>
      );
    case 'checking':
      return (
        <p role="status" className={TEXT}>
          Checking sign-in
        </p>
      );
    case 'signed_in':
      return <SignOut operator={operator} email={session.email} />;
    case 'signed_out':
      return (
        <div className="space-y-4">
          {session.linkFailed && (
            <ErrorState headingLevel={3}
              title="That sign-in link did not work"
              message="A link works once, for an hour, in the browser that asked for it. Ask for a new one."
            />
          )}
          <LinkForm operator={operator} />
        </div>
      );
  }
};

export const SignInCard: React.FC<SignInCardProps> = ({ operator }) => (
  <Card>
    <h2 className="text-base font-bold font-display text-white mb-4">Operator sign-in</h2>
    <SessionPanel operator={operator} />
  </Card>
);
