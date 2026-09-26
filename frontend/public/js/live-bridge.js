/**
 * live-bridge.js — SafeSync
 * Bridges the custom professional frontend design with the live FastAPI backend.
 * Replaces static mock figures, dummy videos, and placeholder tables with real-time
 * camera streams, ByteTrack worker compliance overlays, risk scores, and alert actions.
 */

(function () {
  const API_HOST = window.location.hostname || 'localhost';
  const API_BASE = `http://${API_HOST}:8000`;
  const WS_URL = `ws://${API_HOST}:8000/api/ws/events`;

  let currentCameraId = 'camera_01';
  let camerasList = [];
  let ws = null;
  let isPaused = false;

  // ─── Utility Helpers ────────────────────────────────────────────────────────
  function formatTime(isoOrTimestamp) {
    if (!isoOrTimestamp) return '--:--:--';
    const d = typeof isoOrTimestamp === 'number' ? new Date(isoOrTimestamp * 1000) : new Date(isoOrTimestamp);
    return isNaN(d.getTime()) ? '--:--:--' : d.toTimeString().split(' ')[0];
  }

  // ─── 1. Real-time Clock in Top Header ──────────────────────────────────────
  function startClock() {
    function tick() {
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];
      const dateStr = now.toLocaleDateString('en-GB', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });

      document.querySelectorAll('.font-mono-nums').forEach((el) => {
        if (el.textContent && /^\d{2}:\d{2}:\d{2}$/.test(el.textContent.trim())) {
          el.textContent = timeStr;
        }
      });
    }
    setInterval(tick, 1000);
    tick();
  }

  // ─── 2. Health & Status Indicators ─────────────────────────────────────────
  async function updateHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        // Update header badges
        document.querySelectorAll('header .flex.items-center.gap-1\\.5, header [class*="bg-emerald-50"]').forEach((badge) => {
          const text = badge.textContent || '';
          if (text.includes('API')) {
            badge.className = 'flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md';
            const span = badge.querySelector('.w-2.h-2');
            if (span) span.className = 'w-2 h-2 rounded-full bg-emerald-500';
            const statusSpan = badge.querySelector('.font-normal');
            if (statusSpan) statusSpan.textContent = 'Online';
          }
          if (text.includes('AI Engine')) {
            const isReady = data.ai_engine === 'Connected' || data.ai_engine === 'Ready';
            badge.className = isReady
              ? 'flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md'
              : 'flex items-center gap-1.5 px-2.5 py-1 bg-amber-50/80 border border-amber-100 rounded-md';
            const span = badge.querySelector('.w-2.h-2');
            if (span) span.className = `w-2 h-2 rounded-full ${isReady ? 'bg-emerald-500' : 'bg-amber-500'}`;
            const statusSpan = badge.querySelector('.font-normal');
            if (statusSpan) statusSpan.textContent = data.ai_engine || 'Ready';
          }
          if (text.includes('Database')) {
            const isConnected = data.database === 'connected';
            badge.className = isConnected
              ? 'flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md'
              : 'flex items-center gap-1.5 px-2.5 py-1 bg-rose-50/80 border border-rose-100 rounded-md';
            const span = badge.querySelector('.w-2.h-2');
            if (span) span.className = `w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`;
            const statusSpan = badge.querySelector('.font-normal');
            if (statusSpan) statusSpan.textContent = isConnected ? 'Connected' : 'Disconnected';
          }
        });
      }
    } catch (err) {
      // Backend unreachable
      document.querySelectorAll('header .flex.items-center.gap-1\\.5').forEach((badge) => {
        if (badge.textContent && badge.textContent.includes('API')) {
          badge.className = 'flex items-center gap-1.5 px-2.5 py-1 bg-rose-50/80 border border-rose-100 rounded-md';
          const span = badge.querySelector('.w-2.h-2');
          if (span) span.className = 'w-2 h-2 rounded-full bg-rose-500';
          const statusSpan = badge.querySelector('.font-normal');
          if (statusSpan) statusSpan.textContent = 'Offline';
        }
      });
    }
  }

  // ─── 3. Cameras List & Video Feeds ─────────────────────────────────────────
  async function loadCameras() {
    try {
      const res = await fetch(`${API_BASE}/api/cameras`);
      if (!res.ok) return;
      camerasList = await res.json();
      if (!Array.isArray(camerasList) || camerasList.length === 0) return;

      // Populate camera dropdown
      const select = document.querySelector('select');
      if (select && select.innerHTML.includes('CAM-')) {
        select.innerHTML = camerasList
          .map(
            (c) =>
              `<option value="${c.camera_id}" ${c.camera_id === currentCameraId ? 'selected' : ''}>` +
              `${c.camera_id.toUpperCase().replace('_', '-')} - ${c.name}` +
              `</option>`
          )
          .join('');

        select.addEventListener('change', (e) => {
          currentCameraId = e.target.value;
          updateLiveFeed();
        });
      }

      // Update Active Cameras Metric Card
      const activeCount = camerasList.filter((c) => c.enabled && (c.state === 'ACTIVE' || c.state === 'DEGRADED')).length;
      const totalCount = camerasList.length;

      document.querySelectorAll('.text-xl.font-extrabold').forEach((el) => {
        const parent = el.closest('.bg-white, .bg-surface-container-lowest');
        if (parent && parent.textContent.includes('Active Cameras')) {
          el.textContent = `${activeCount} / ${totalCount}`;
          const subText = parent.querySelector('.text-\\[10px\\].text-slate-400, .font-label-sm');
          if (subText) subText.textContent = `${activeCount} online • ${totalCount - activeCount} offline`;
          const progressBar = parent.querySelector('.bg-emerald-500');
          if (progressBar) progressBar.style.width = `${Math.round((activeCount / totalCount) * 100)}%`;
        }
      });

      updateLiveFeed();
    } catch {
      // Keep static view if network fails
    }
  }

  function updateLiveFeed() {
    if (isPaused) return;

    // Center Main Camera Feed image
    const mainFeedContainer = document.querySelector('.aspect-\\[16\\/9\\], .aspect-video');
    if (!mainFeedContainer) return;

    let feedImg = mainFeedContainer.querySelector('img');
    if (feedImg) {
      const streamUrl = `${API_BASE}/api/cameras/${currentCameraId}/stream`;
      if (!feedImg.src.includes(`/api/cameras/${currentCameraId}/stream`)) {
        feedImg.src = streamUrl;
        feedImg.classList.remove('opacity-90', 'brightness-95');
        feedImg.style.objectFit = 'contain';
        feedImg.style.backgroundColor = '#020617';

        feedImg.onerror = () => {
          // If stream fails, fallback to snapshot
          feedImg.src = `${API_BASE}/api/cameras/${currentCameraId}/snapshot?t=${Date.now()}`;
        };
      }
    }
  }

  // ─── 4. Live Worker Compliance & Bounding Boxes ────────────────────────────
  async function updateWorkersAndCompliance() {
    try {
      const res = await fetch(`${API_BASE}/api/compliance/live`);
      if (!res.ok) return;
      const data = await res.json();
      if (!data) return;

      const workers = Array.isArray(data.workers) ? data.workers : [];
      const summary = data.summary || {
        total_workers: workers.length,
        compliant_workers: workers.filter((w) => w.is_compliant).length,
        non_compliant_workers: workers.filter((w) => !w.is_compliant).length,
        compliance_percentage: workers.length ? Math.round((workers.filter((w) => w.is_compliant).length / workers.length) * 100) : 100,
        itemized_compliance: {
          helmet: { present: 0, absent: 0, unknown: 0 },
          vest: { present: 0, absent: 0, unknown: 0 },
          gloves: { present: 0, absent: 0, unknown: 0 },
          footwear: { present: 0, absent: 0, unknown: 0 },
        },
      };

      // 1. Update Tracked Workers Metric Card
      document.querySelectorAll('.text-xl.font-extrabold').forEach((el) => {
        const parent = el.closest('.bg-white, .bg-surface-container-lowest');
        if (parent && parent.textContent.includes('Tracked Workers')) {
          el.textContent = `${summary.total_workers}`;
          const subText = parent.querySelector('.text-\\[10px\\].text-slate-400');
          if (subText) subText.textContent = `Live on active cameras`;
        }
      });

      // 2. Update PPE Compliance Metric Card
      document.querySelectorAll('.text-xl.font-extrabold').forEach((el) => {
        const parent = el.closest('.bg-white, .bg-surface-container-lowest');
        if (parent && parent.textContent.includes('PPE Compliance')) {
          el.textContent = `${Math.round(summary.compliance_percentage)}%`;
          const subText = parent.querySelector('.text-\\[10px\\].text-rose-500, .text-\\[10px\\].text-emerald-500');
          if (subText) {
            subText.textContent = `${summary.non_compliant_workers} violations`;
            subText.className = summary.non_compliant_workers > 0 ? 'text-[10px] text-rose-500 font-medium mt-0.5' : 'text-[10px] text-emerald-500 font-medium mt-0.5';
          }
          const donut = parent.querySelector('.text-emerald-500[stroke-dasharray]');
          if (donut) {
            const pct = Math.round(summary.compliance_percentage);
            donut.setAttribute('stroke-dasharray', `${pct}, 100`);
          }
        }
      });

      // 3. Update Stream bottom metrics bar
      const bottomBar = document.querySelector('.absolute.bottom-0.inset-x-0');
      if (bottomBar) {
        const workerCountEl = bottomBar.querySelector('.text-emerald-400');
        if (workerCountEl) workerCountEl.textContent = `${summary.total_workers}`;
      }

      // 4. Update Dynamic Worker Bounding Box Overlays on Stream (if annotated stream not used)
      const feedContainer = document.querySelector('.aspect-\\[16\\/9\\], .aspect-video');
      if (feedContainer && workers.length > 0) {
        // Clear mock boxes
        feedContainer.querySelectorAll('.dynamic-worker-box').forEach((b) => b.remove());
        // Hide hardcoded static dummy boxes if present
        feedContainer.querySelectorAll('.absolute[style*="left: 22.5%"], .absolute[style*="left: 38%"], .absolute[style*="left: 52%"]').forEach((b) => {
          b.style.display = 'none';
        });

        // Add real worker overlays
        workers.forEach((w) => {
          if (!w.bbox || w.bbox.length < 4) return;
          const [x1, y1, x2, y2] = w.bbox;
          // Normalize (assuming 1280x720 if absolute pixels)
          const leftPct = x1 > 1 ? (x1 / 1280) * 100 : x1 * 100;
          const topPct = y1 > 1 ? (y1 / 720) * 100 : y1 * 100;
          const widthPct = x2 > 1 ? ((x2 - x1) / 1280) * 100 : (x2 - x1) * 100;
          const heightPct = y2 > 1 ? ((y2 - y1) / 720) * 100 : (y2 - y1) * 100;

          const isCompliant = w.is_compliant;
          const colorClass = isCompliant ? 'border-emerald-500' : 'border-rose-500';
          const bgClass = isCompliant ? 'bg-emerald-600' : 'bg-rose-600';

          const box = document.createElement('div');
          box.className = `absolute dynamic-worker-box pointer-events-none transition-all duration-300`;
          box.style.left = `${Math.max(0, leftPct)}%`;
          box.style.top = `${Math.max(0, topPct)}%`;
          box.style.width = `${Math.max(3, widthPct)}%`;
          box.style.height = `${Math.max(5, heightPct)}%`;

          const ppe = w.ppe_status || {};
          const renderItem = (label, status) => {
            const icon = status === 'PRESENT' ? '<span class="text-emerald-400 font-bold">✓</span>' : status === 'ABSENT' ? '<span class="text-rose-400 font-bold">✕</span>' : '<span class="text-amber-400 font-bold">?</span>';
            return `<div>${label}: ${icon}</div>`;
          };

          box.innerHTML = `
            <div class="w-full h-full border-2 ${colorClass} relative shadow-sm">
              <div class="absolute -top-4 left-0 ${bgClass} text-white text-[8px] font-bold px-1 rounded-t">
                ID: ${w.track_id}
              </div>
              <div class="absolute top-0 -right-20 bg-black/85 backdrop-blur-sm border ${colorClass} text-white text-[8px] rounded px-1.5 py-1 whitespace-nowrap leading-tight">
                ${renderItem('Helmet', ppe.helmet)}
                ${renderItem('Vest', ppe.vest)}
                ${renderItem('Gloves', ppe.gloves)}
                ${renderItem('Shoes', ppe.footwear)}
              </div>
            </div>
          `;
          feedContainer.appendChild(box);
        });
      }
    } catch {
      // Tolerate temporary network drop
    }
  }

  // ─── 5. Risk Summary & Smart Alerts ────────────────────────────────────────
  async function updateRiskAndAlerts() {
    try {
      const [riskRes, alertsRes] = await Promise.all([
        fetch(`${API_BASE}/api/risk/summary`),
        fetch(`${API_BASE}/api/alerts?limit=15`),
      ]);

      let activeAlertsCount = 0;

      if (riskRes.ok) {
        const risk = await riskRes.json();
        activeAlertsCount = risk.active_alerts ?? 0;

        // Update Active Alerts Metric Card
        document.querySelectorAll('.text-xl.font-extrabold').forEach((el) => {
          const parent = el.closest('.bg-white, .bg-surface-container-lowest');
          if (parent && parent.textContent.includes('Active Alerts')) {
            el.textContent = `${activeAlertsCount}`;
            const sub = parent.querySelector('.text-\\[10px\\].text-rose-600, .text-\\[10px\\].text-slate-400');
            if (sub) {
              sub.textContent = activeAlertsCount > 0 ? `${activeAlertsCount} Need attention` : 'All zones normal';
            }
          }
        });

        // Update Fire & Smoke Metrics
        document.querySelectorAll('.text-xl.font-extrabold').forEach((el) => {
          const parent = el.closest('.bg-white, .bg-surface-container-lowest');
          if (parent && parent.textContent.includes('Fire Incidents')) {
            el.textContent = `${risk.critical_fire ?? 0}`;
          }
          if (parent && parent.textContent.includes('Smoke Incidents')) {
            el.textContent = `${risk.critical_smoke ?? 0}`;
          }
        });

        // Update Header & Sidebar notification pills
        document.querySelectorAll('.bg-rose-500.text-white.font-bold, .bg-error.text-on-error').forEach((pill) => {
          if (pill.classList.contains('rounded-full')) {
            pill.textContent = `${activeAlertsCount}`;
          }
        });
      }

      if (alertsRes.ok) {
        const alerts = await alertsRes.json();
        if (Array.isArray(alerts) && alerts.length > 0) {
          renderAlertsList(alerts);
        }
      }
    } catch {
      // Tolerate drop
    }
  }

  function renderAlertsList(alerts) {
    const listContainer = document.querySelector('.space-y-2\\.5, tbody');
    if (!listContainer) return;

    // If it's a sidebar incident feed list
    if (listContainer.classList.contains('space-y-2.5')) {
      listContainer.innerHTML = alerts
        .slice(0, 5)
        .map((a) => {
          const isHigh = a.severity === 'CRITICAL' || a.severity === 'HIGH';
          const sevColor = isHigh ? 'rose' : a.severity === 'MEDIUM' ? 'amber' : 'sky';
          const time = formatTime(a.timestamp_utc || a.created_at);

          return `
          <div class="p-2.5 rounded-lg border border-${sevColor}-100 bg-${sevColor}-50/30 flex items-start gap-2.5 transition hover:shadow-sm">
            <span class="w-2 h-2 rounded-full bg-${sevColor}-500 mt-1 flex-shrink-0"></span>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-mono-nums text-[10px] text-slate-500">${time}</span>
                <span class="bg-${sevColor}-500 text-white font-bold text-[8px] px-1.5 py-0.5 rounded tracking-wide">${a.severity}</span>
                <span class="text-[9px] font-semibold text-slate-500 ml-auto">${a.status}</span>
              </div>
              <div class="font-bold text-slate-800 text-[11px] mt-0.5">${a.title || a.event_type.replace(/_/g, ' ')}</div>
              <p class="text-[10px] text-slate-500 leading-snug">${a.message || 'Anomaly detected'}</p>
              <div class="flex items-center justify-between mt-1 pt-1 border-t border-slate-100">
                <p class="text-[9px] text-slate-400">${a.camera_id} | ${a.zone_id}</p>
                <div class="flex items-center gap-1">
                  ${
                    a.status === 'ACTIVE'
                      ? `<button onclick="window.__safesyncAction('${a.alert_id}', 'acknowledge')" class="px-1.5 py-0.5 bg-amber-500 hover:bg-amber-600 text-white text-[8px] font-semibold rounded cursor-pointer">Ack</button>`
                      : ''
                  }
                  ${
                    a.status !== 'RESOLVED'
                      ? `<button onclick="window.__safesyncAction('${a.alert_id}', 'resolve')" class="px-1.5 py-0.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[8px] font-semibold rounded cursor-pointer">Resolve</button>`
                      : ''
                  }
                </div>
              </div>
            </div>
          </div>`;
        })
        .join('');
    }
  }

  // ─── 6. Action Handlers: Acknowledge & Resolve ──────────────────────────────
  window.__safesyncAction = async function (alertId, action) {
    try {
      const endpoint = action === 'acknowledge' ? `/api/incidents/${alertId}/acknowledge` : `/api/incidents/${alertId}/resolve`;
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: `Actioned via Dashboard by Operator` }),
      });
      if (res.ok) {
        updateRiskAndAlerts();
      }
    } catch (err) {
      console.error('Error actioning alert:', err);
    }
  };

  // ─── 7. WebSocket Live Updates ──────────────────────────────────────────────
  function connectWebSocket() {
    try {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        // Update WebSocket status badge in header
        document.querySelectorAll('header .flex.items-center.gap-1\\.5').forEach((badge) => {
          if (badge.textContent && badge.textContent.includes('WebSocket')) {
            badge.className = 'flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md';
            const span = badge.querySelector('.w-2.h-2');
            if (span) span.className = 'w-2 h-2 rounded-full bg-emerald-500';
            const statusSpan = badge.querySelector('.font-normal');
            if (statusSpan) statusSpan.textContent = 'Connected';
          }
        });
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === 'compliance_update') {
            updateWorkersAndCompliance();
          } else if (msg.event === 'risk_update' || msg.event === 'alert_created' || msg.event === 'incident_updated') {
            updateRiskAndAlerts();
          } else if (msg.event === 'camera_status') {
            loadCameras();
          }
        } catch {
          // Ignore parse errors
        }
      };

      ws.onclose = () => {
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setTimeout(connectWebSocket, 5000);
    }
  }

  // ─── Initialize ─────────────────────────────────────────────────────────────
  function init() {
    startClock();
    updateHealth();
    loadCameras();
    updateWorkersAndCompliance();
    updateRiskAndAlerts();
    connectWebSocket();

    // Regular polling intervals
    setInterval(updateHealth, 5000);
    setInterval(updateWorkersAndCompliance, 1500);
    setInterval(updateRiskAndAlerts, 3000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
