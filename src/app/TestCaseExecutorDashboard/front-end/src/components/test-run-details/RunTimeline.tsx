import React, { useEffect, useState } from "react";
import styles from "./runtimeline.module.css";
import { API_ENDPOINTS } from "../../config/api";
import { redirectToLogin } from "../../utils/auth";

/* ===== TYPES ===== */

interface TimelineEvent {
  conversation_id: number;
  metric_name: string;
  plan_name: string;
  prompt_ts: string | null;
  response_ts: string | null;
}

interface Props {
  runName: string;
  hoveredMetric: string | null;
  hoveredPlan?: string | null;
  onHoverPlan?: (plan: string | null) => void;
  onHoverMetric: (metric: string | null) => void;
  onDurationCalculated?: (duration: string) => void;
}

/* ===== COMPONENT ===== */

const GAP_THRESHOLD_MS = 5000; // 5 seconds

const RunTimeline: React.FC<Props> = ({ runName, hoveredMetric, onHoverMetric, onDurationCalculated }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  const getAuthHeaders = (): HeadersInit => {
    const token = localStorage.getItem("access_token");
    return token
      ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
      : { "Content-Type": "application/json" };
  };

  useEffect(() => {
    fetch(API_ENDPOINTS.GET_TIMELINE(runName), {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Unauthorized");
        }
        return res.json();
      })
      .then(setEvents);
  }, [runName]);

  /* ================= GROUP INTO SEQUENTIAL PLAN BLOCKS ================= */
  const planBlocks = buildPlanBlocks(events);

  const totalDuration = planBlocks.reduce(
    (sum, block) => sum + getPlanDuration(block.events),
    0
  );

  useEffect(() => {
    onDurationCalculated?.(formatDuration(totalDuration));
  }, [onDurationCalculated, totalDuration]);

  if (events.length === 0) return null;

  const eventsByPlan: Record<string, TimelineEvent[]> = Object.fromEntries(
    planBlocks.map(b => [b.key, b.events])
  );
  const planDisplayNames: Record<string, string> = Object.fromEntries(
    planBlocks.map(b => [b.key, b.name])
  );
  const planNames = planBlocks.map(b => b.key);

  if (planNames.length === 0) return null;

  /* ================= CALCULATE GAPS BETWEEN BLOCKS ================= */
  const planGaps = planNames.slice(0, -1).map((plan, i) => {
    const currentPlan = eventsByPlan[plan];
    const nextPlan = eventsByPlan[planNames[i + 1]];

    if (!currentPlan.length || !nextPlan.length) return 0;

    const lastEventOfCurrent = currentPlan.reduce((latest, event) => {
      const time = new Date(event.response_ts!).getTime();
      return time > latest ? time : latest;
    }, 0);

    const firstEventOfNext = nextPlan.reduce((earliest, event) => {
      const time = new Date(event.prompt_ts!).getTime();
      return time < earliest ? time : earliest;
    }, Infinity);

    return firstEventOfNext - lastEventOfCurrent;
  });

  return (
    <div className={styles.timelineCard}>
      <div className={styles.timelineHeader} />

      <div className={styles.planRow}>
        {planNames.map((planKey, index) => {
          const planEvents = eventsByPlan[planKey];

          const start = getPlanStart(planEvents);
          const total = getPlanDuration(planEvents) || 1;

          if (total <= 0) return null;

          return (
            <React.Fragment key={planKey}>
              <div className={styles.planBlock}>
                <div className={styles.planHeader}>
                  {planDisplayNames[planKey]}
                  <div className={styles.duration}>{formatDuration(total)}</div>
                </div>

                <div className={styles.timeline}>
                  {planEvents.map(e => {
                    const prompt = getTimestamp(e.prompt_ts);
                    const response = getTimestamp(e.response_ts);
                    const left = ((prompt - start) / total) * 100;
                    const width = ((response - prompt) / total) * 100;

                    return (
                      <div
                        key={e.conversation_id}
                        className={styles.block}
                        style={{
                          left: `${left}%`,
                          width: `${width}%`,
                          opacity:
                            hoveredMetric === null
                              ? 0.3
                              : hoveredMetric === e.metric_name
                              ? 1
                              : 0.25,
                        }}
                        onMouseEnter={() => onHoverMetric(e.metric_name)}
                        onMouseLeave={() => onHoverMetric(null)}
                      />
                    );
                  })}
                </div>

                <div className={styles.scale}>
                  {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
                    <div
                      key={i}
                      className={styles.scaleItem}
                      style={{ left: `${p * 100}%` }}
                    >
                      {p === 0 ? "0" : formatDuration(total * p)}
                    </div>
                  ))}
                </div>
              </div>

              {index < planNames.length - 1 && (
                <div
                  className={styles.planConnector}
                  data-gap={`${formatDuration(planGaps[index])} gap`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "-";
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function getTimestamp(value: string | null): number {
  if (!value) return NaN;
  return new Date(value).getTime();
}

function hasCompleteTiming(event: TimelineEvent): boolean {
  return Number.isFinite(getTimestamp(event.prompt_ts)) && Number.isFinite(getTimestamp(event.response_ts));
}

function getPlanStart(planEvents: TimelineEvent[]): number {
  return Math.min(...planEvents.map(e => getTimestamp(e.prompt_ts)));
}

function getPlanEnd(planEvents: TimelineEvent[]): number {
  return Math.max(...planEvents.map(e => getTimestamp(e.response_ts)));
}

function getPlanDuration(planEvents: TimelineEvent[]): number {
  const start = getPlanStart(planEvents);
  const end = getPlanEnd(planEvents);
  const duration = end - start;
  return Number.isFinite(duration) && duration > 0 ? duration : 0;
}

function buildPlanBlocks(events: TimelineEvent[]): { key: string; name: string; events: TimelineEvent[] }[] {
  const sortedEvents = events
    .filter(hasCompleteTiming)
    .sort((a, b) => getTimestamp(a.prompt_ts) - getTimestamp(b.prompt_ts));

  const planBlocks: { key: string; name: string; events: TimelineEvent[] }[] = [];

  for (const event of sortedEvents) {
    const last = planBlocks[planBlocks.length - 1];
    const eventTime = getTimestamp(event.prompt_ts);

    if (last && last.name === event.plan_name) {
      const lastResponseTime = getPlanEnd(last.events);
      if (eventTime - lastResponseTime < GAP_THRESHOLD_MS) {
        // Continuous run: same plan remains one visible timeline block.
        last.events.push(event);
        continue;
      }
    }

    const count = planBlocks.filter(b => b.name === event.plan_name).length;
    planBlocks.push({
      key: `${event.plan_name}__${count}`,
      name: event.plan_name,
      events: [event],
    });
  }

  return planBlocks;
}

export default RunTimeline;
