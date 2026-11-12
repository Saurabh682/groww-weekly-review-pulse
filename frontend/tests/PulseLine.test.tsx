import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PulseLine } from '../src/pulseline/PulseLine';
import { FIXTURE_WEEKS } from '../src/data/fixtures/pulseNote';

describe('PulseLine Component', () => {
  it('renders 12 weekly beat nodes', () => {
    render(<PulseLine weeks={FIXTURE_WEEKS} threshold={3.8} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(12);
  });

  it('renders aria labels indicating ratings and threshold warning', () => {
    render(<PulseLine weeks={FIXTURE_WEEKS} threshold={3.8} />);
    // Check for amber/threshold beat (e.g. 14 Sep rating is 3.7)
    const amberBeat = screen.getByLabelText(/Week of 14 Sep: Rating 3.7 stars \(below 3.8 threshold\)/i);
    expect(amberBeat).toBeInTheDocument();

    // Check for current beat (09 Nov)
    const currentBeat = screen.getByLabelText(/Week of 09 Nov:.*\(Current Week\)/i);
    expect(currentBeat).toBeInTheDocument();
  });

  it('shows tooltip on focus and mouse hover', () => {
    render(<PulseLine weeks={FIXTURE_WEEKS} threshold={3.8} />);
    const firstBeat = screen.getByLabelText(/Week of 24 Aug/i);
    fireEvent.mouseEnter(firstBeat);
    expect(screen.getByText('Week of 24 Aug')).toBeInTheDocument();
  });
});
