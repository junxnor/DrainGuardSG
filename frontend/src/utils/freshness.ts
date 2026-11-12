import type { RiskOverview, StationRisk } from '../store/appStore'

// Must match STALE_AFTER in backend/services/risk_service.py
export const STALE_AFTER_MINUTES = 30

export function minutesSince(iso: string | null | undefined, now: number): number | null {
  if (!iso) return null
  const t = Date.parse(iso)
  return Number.isNaN(t) ? null : Math.floor((now - t) / 60000)
}

function staleNote(minutes: number) {
  return `Newest reading is ${minutes} minutes old`
}

/**
 * Re-check freshness in the browser. The server already marks old data as no_data,
 * but if refreshes fail while the page stays open, the last response would otherwise
 * keep showing as current.
 */
export function freshStationRisks(risks: StationRisk[], now: number): StationRisk[] {
  return risks.map((r) => {
    const age = minutesSince(r.observed_at, now)
    if (r.data_status !== 'ok' || age === null || age <= STALE_AFTER_MINUTES) return r
    return { ...r, data_status: 'no_data', risk_level: 'no_data', data_note: staleNote(age) }
  })
}

export function freshOverview(overview: RiskOverview | null, now: number): RiskOverview | null {
  if (!overview) return overview
  const age = minutesSince(overview.last_updated, now)
  if (overview.data_status !== 'ok' || age === null || age <= STALE_AFTER_MINUTES) return overview
  return { ...overview, data_status: 'no_data', overall_risk: 'no_data', data_note: staleNote(age) }
}

const sgtTime = new Intl.DateTimeFormat('en-SG', {
  timeZone: 'Asia/Singapore',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

/** "05:20 SGT" from an ISO timestamp, regardless of the viewer's own time zone */
export function formatSgtTime(iso: string | null | undefined): string | null {
  if (!iso) return null
  const t = Date.parse(iso)
  return Number.isNaN(t) ? null : `${sgtTime.format(t)} SGT`
}
