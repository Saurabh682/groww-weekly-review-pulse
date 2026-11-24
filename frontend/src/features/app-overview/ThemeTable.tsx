import React from 'react';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { PulseTheme } from '../../data/types';
import { formatIndianNumber, formatRating, formatShare } from '../../lib/format';
import { SectionTitle } from '../../components/SectionTitle';

const PERCENT = 100;

interface ThemeTableProps {
  themes: PulseTheme[];
}

export const ThemeTable: React.FC<ThemeTableProps> = ({ themes }) => (
  <section>
    <SectionTitle>Themes</SectionTitle>
    <Card className="!p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-border bg-sidebar/90 text-[11px] font-mono font-bold text-text-muted uppercase tracking-wider">
              <th className="py-3 px-4">Rank</th>
              <th className="py-3 px-4">Theme</th>
              <th className="py-3 px-4 text-right">Review Share</th>
              <th className="py-3 px-4 text-center">Avg Rating</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {themes.map((theme, index) => (
              <tr key={theme.label}>
                <td className="py-3.5 px-4 font-mono font-bold text-white">#{index + 1}</td>
                <td className="py-3.5 px-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold font-display text-white text-xs">{theme.label}</span>
                    {theme.is_top3 && <Badge variant="teal">In Pulse</Badge>}
                  </div>
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono">
                  <div className="font-bold text-white">{formatShare(theme.share_pct * PERCENT)}</div>
                  <div className="text-[10px] text-text-muted">{formatIndianNumber(theme.review_count)} revs</div>
                </td>
                <td className="py-3.5 px-4 text-center font-mono font-bold text-friction-dark whitespace-nowrap">
                  {formatRating(theme.avg_rating)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  </section>
);
