/**
 * El-Sharnouby Group Executive Enterprise Platform
 * Frontend Application Controller & Chart Manager
 */

// Global State
const state = {
  activeView: 'view-ceo-home',
  filters: {
    start_date: null,
    end_date: null,
    channels: [],
    families: [],
    locations: [],
    cust_types: [],
    hide_returns: false,
  },
  availableFilters: {},
  charts: {},
  chatHistory: [],
  chatScope: 'Active Filtered Slice',
  explorer: {
    page: 1,
    pageSize: 50,
    search: '',
    totalPages: 1,
  },
  dataCache: {},
};

// Brand Colors
const COLORS = {
  navy: '#0b1f3a',
  navyLight: '#16385c',
  gold: '#c9a227',
  goldLight: '#f5d77f',
  teal: '#1a7a6d',
  tealLight: '#2ee59d',
  coral: '#c45c26',
  coralLight: '#ff7a59',
  slate: '#4a6fa5',
  slateLight: '#90cdf4',
  textMuted: '#94a3b8',
  border: '#183358',
};

// ---------------------------------------------------------------------------
// Chart.js Default Dark Theme Setup
// ---------------------------------------------------------------------------
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(6, 14, 29, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = '#1e3a5f';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.titleColor = '#f5d77f';

function destroyChart(id) {
  if (state.charts[id]) {
    state.charts[id].destroy();
    delete state.charts[id];
  }
}

// ---------------------------------------------------------------------------
// Formatting Helpers
// ---------------------------------------------------------------------------
function fmtEGP(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const abs = Math.abs(val);
  if (abs >= 1_000_000) return (val / 1_000_000).toFixed(2) + 'M EGP';
  if (abs >= 1_000) return (val / 1_000).toFixed(1) + 'K EGP';
  return Number(val).toLocaleString() + ' EGP';
}

function fmtPct(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return (val * 100).toFixed(1) + '%';
}

function renderDeltaBadge(delta) {
  if (!delta) return '';
  const isNeg = delta.startsWith('-');
  const cls = isNeg ? 'delta-negative' : 'delta-positive';
  const icon = isNeg ? 'fa-arrow-down' : 'fa-arrow-up';
  return `<span class="metric-delta ${cls}"><i class="fa-solid ${icon}"></i> ${delta}</span>`;
}

function renderMetricCard(label, value, delta, iconName = 'fa-chart-simple') {
  return `
    <div class="metric-card">
      <div class="metric-header">
        <span class="metric-label">${label}</span>
        <i class="fa-solid ${iconName} metric-icon"></i>
      </div>
      <div class="metric-value">${value}</div>
      ${renderDeltaBadge(delta)}
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Initial Setup & Filter Fetching
// ---------------------------------------------------------------------------
async function initApp() {
  setupNavigation();
  setupFilterControls();
  setupExplorer();
  setupChat();

  try {
    const res = await fetch('/api/filters');
    const data = await res.json();
    state.availableFilters = data;

    // Set initial date range from API min/max
    state.filters.start_date = data.date_range.min;
    state.filters.end_date = data.date_range.max;

    document.getElementById('filter-start-date').value = data.date_range.min;
    document.getElementById('filter-end-date').value = data.date_range.max;

    // Populate Multi-select Chips
    renderChips('container-channels', data.channels, 'channels');
    renderChips('container-families', data.families, 'families');
    renderChips('container-locations', data.locations, 'locations');
    renderChips('container-cust-types', data.cust_types, 'cust_types');

    // Load initial workspace
    await loadActiveWorkspace();
  } catch (err) {
    console.error('Failed to initialize dashboard filters:', err);
  }
}

function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach((item) => {
    item.addEventListener('click', () => {
      navItems.forEach((i) => i.classList.remove('active'));
      item.classList.add('active');

      const targetView = item.getAttribute('data-view');
      state.activeView = targetView;

      document.querySelectorAll('.workspace-view').forEach((v) => v.classList.remove('active'));
      const activeEl = document.getElementById(targetView);
      if (activeEl) activeEl.classList.add('active');

      // Update heading text
      const viewTitle = item.textContent.replace('AI Advisor', '').trim();
      document.getElementById('page-heading').textContent = viewTitle;

      loadActiveWorkspace();
    });
  });
}

function renderChips(containerId, options, filterKey) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  // Select all by default
  state.filters[filterKey] = [...options];

  options.forEach((opt) => {
    const chip = document.createElement('div');
    chip.className = 'chip selected';
    chip.textContent = opt;
    chip.addEventListener('click', () => {
      chip.classList.toggle('selected');
      const idx = state.filters[filterKey].indexOf(opt);
      if (idx > -1) {
        state.filters[filterKey].splice(idx, 1);
      } else {
        state.filters[filterKey].push(opt);
      }
      updateChipCounters();
    });
    container.appendChild(chip);
  });
  updateChipCounters();
}

function updateChipCounters() {
  const chCount = state.filters.channels.length;
  const famCount = state.filters.families.length;
  const locCount = state.filters.locations.length;
  const ctCount = state.filters.cust_types.length;

  document.getElementById('count-selected-channels').textContent =
    chCount === state.availableFilters.channels?.length ? 'All' : chCount;
  document.getElementById('count-selected-families').textContent =
    famCount === state.availableFilters.families?.length ? 'All' : famCount;
  document.getElementById('count-selected-locations').textContent =
    locCount === state.availableFilters.locations?.length ? 'All' : locCount;
  document.getElementById('count-selected-cust-types').textContent =
    ctCount === state.availableFilters.cust_types?.length ? 'All' : ctCount;
}

function setupFilterControls() {
  // Preset buttons
  document.querySelectorAll('.btn-preset').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-preset').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      const preset = btn.getAttribute('data-preset');
      const minD = state.availableFilters.date_range.min;
      const maxD = state.availableFilters.date_range.max;

      const maxDateObj = new Date(maxD);

      if (preset === 'all') {
        state.filters.start_date = minD;
        state.filters.end_date = maxD;
      } else if (preset === '2026') {
        state.filters.start_date = '2026-01-01';
        state.filters.end_date = maxD;
      } else if (preset === '2025') {
        state.filters.start_date = '2025-01-01';
        state.filters.end_date = '2025-12-31';
      } else if (preset === '2024') {
        state.filters.start_date = '2024-01-01';
        state.filters.end_date = '2024-12-31';
      } else if (preset === '90d') {
        const d = new Date(maxDateObj);
        d.setDate(d.getDate() - 90);
        state.filters.start_date = d.toISOString().split('T')[0];
        state.filters.end_date = maxD;
      } else if (preset === '30d') {
        const d = new Date(maxDateObj);
        d.setDate(d.getDate() - 30);
        state.filters.start_date = d.toISOString().split('T')[0];
        state.filters.end_date = maxD;
      }

      document.getElementById('filter-start-date').value = state.filters.start_date;
      document.getElementById('filter-end-date').value = state.filters.end_date;
    });
  });

  // Date input change
  document.getElementById('filter-start-date').addEventListener('change', (e) => {
    state.filters.start_date = e.target.value;
  });
  document.getElementById('filter-end-date').addEventListener('change', (e) => {
    state.filters.end_date = e.target.value;
  });

  // Exclude returns toggle
  document.getElementById('filter-hide-returns').addEventListener('change', (e) => {
    state.filters.hide_returns = e.target.checked;
  });

  // Apply button
  document.getElementById('btn-apply-filters').addEventListener('click', () => {
    loadActiveWorkspace();
  });

  // Reset button
  document.getElementById('btn-reset-filters').addEventListener('click', () => {
    state.filters.start_date = state.availableFilters.date_range.min;
    state.filters.end_date = state.availableFilters.date_range.max;
    state.filters.hide_returns = false;
    document.getElementById('filter-start-date').value = state.filters.start_date;
    document.getElementById('filter-end-date').value = state.filters.end_date;
    document.getElementById('filter-hide-returns').checked = false;

    renderChips('container-channels', state.availableFilters.channels, 'channels');
    renderChips('container-families', state.availableFilters.families, 'families');
    renderChips('container-locations', state.availableFilters.locations, 'locations');
    renderChips('container-cust-types', state.availableFilters.cust_types, 'cust_types');

    document.querySelectorAll('.btn-preset').forEach((b) => b.classList.remove('active'));
    document.querySelector('.btn-preset[data-preset="all"]').classList.add('active');

    loadActiveWorkspace();
  });
}

// ---------------------------------------------------------------------------
// Workspace Loader Router
// ---------------------------------------------------------------------------
async function loadActiveWorkspace() {
  const reqBody = { ...state.filters };

  if (state.activeView === 'view-ceo-home') {
    await loadCeoHome(reqBody);
  } else if (state.activeView === 'view-sales-command') {
    await loadSalesCommand(reqBody);
  } else if (state.activeView === 'view-products') {
    await loadProducts(reqBody);
  } else if (state.activeView === 'view-customers') {
    await loadCustomers(reqBody);
  } else if (state.activeView === 'view-channels') {
    await loadChannels(reqBody);
  } else if (state.activeView === 'view-operations') {
    await loadOperations(reqBody);
  } else if (state.activeView === 'view-explorer') {
    await loadExplorerData();
  }
}

// ---------------------------------------------------------------------------
// VIEW 1: CEO HOME
// ---------------------------------------------------------------------------
async function loadCeoHome(reqBody) {
  try {
    const res = await fetch('/api/overview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json();

    // Update Top Pill
    document.getElementById('pill-text').textContent = `Filtered (${data.count_view.toLocaleString()} / ${data.count_total.toLocaleString()} lines)`;
    document.getElementById('chat-scope-count').textContent = `${data.count_view.toLocaleString()} lines`;
    document.getElementById('ceo-hero-sub').textContent =
      `Sales-led operating picture for LEO MODA · ${state.filters.start_date} → ${state.filters.end_date} · ${data.count_view.toLocaleString()} invoice lines`;

    // 1. Primary Metrics Row
    const kpis = data.kpis;
    document.getElementById('ceo-metrics-row').innerHTML = `
      ${renderMetricCard('Net Sales', kpis.net.label, kpis.net.delta, 'fa-money-bill-wave')}
      ${renderMetricCard('Gross Profit', kpis.profit.label, kpis.profit.delta, 'fa-coins')}
      ${renderMetricCard('Gross Margin', kpis.margin.label, kpis.margin.delta, 'fa-chart-pie')}
      ${renderMetricCard('Units Sold', kpis.units.label, kpis.units.delta, 'fa-boxes-stacked')}
      ${renderMetricCard('AOV', kpis.aov.label, kpis.aov.delta, 'fa-basket-shopping')}
      ${renderMetricCard('Return Rate', kpis.return_rate.label, kpis.return_rate.delta, 'fa-rotate-left')}
    `;

    // 2. Chart: Revenue vs Gross Profit
    destroyChart('chart-ceo-rev-profit');
    const ctxRevProfit = document.getElementById('chart-ceo-rev-profit').getContext('2d');
    const months = data.monthly_chart.map((d) => d.month);
    const netSales = data.monthly_chart.map((d) => d.net_sales);
    const grossProfit = data.monthly_chart.map((d) => d.gross_profit);

    state.charts['chart-ceo-rev-profit'] = new Chart(ctxRevProfit, {
      type: 'bar',
      data: {
        labels: months,
        datasets: [
          {
            type: 'line',
            label: 'Gross Profit (EGP)',
            data: grossProfit,
            borderColor: COLORS.gold,
            backgroundColor: COLORS.gold,
            borderWidth: 3,
            tension: 0.25,
            yAxisID: 'y1',
          },
          {
            type: 'bar',
            label: 'Net Sales (EGP)',
            data: netSales,
            backgroundColor: 'rgba(22, 56, 92, 0.85)',
            borderColor: '#2b588a',
            borderWidth: 1,
            borderRadius: 4,
            yAxisID: 'y',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' } },
          y: {
            position: 'left',
            grid: { color: 'rgba(255,255,255,0.06)' },
            ticks: { callback: (v) => fmtEGP(v) },
          },
          y1: {
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { callback: (v) => fmtEGP(v) },
          },
        },
      },
    });

    // 3. Chart: Net Sales by Channel
    destroyChart('chart-ceo-channel');
    const ctxChannel = document.getElementById('chart-ceo-channel').getContext('2d');
    const chLabels = data.channel_chart.map((d) => d.channel);
    const chSales = data.channel_chart.map((d) => d.net_sales);

    state.charts['chart-ceo-channel'] = new Chart(ctxChannel, {
      type: 'doughnut',
      data: {
        labels: chLabels,
        datasets: [
          {
            data: chSales,
            backgroundColor: [COLORS.navyLight, COLORS.gold, COLORS.teal, COLORS.coral],
            borderColor: '#0a1628',
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${fmtEGP(ctx.raw)} (${((ctx.raw / chSales.reduce((a, b) => a + b, 0)) * 100).toFixed(1)}%)`,
            },
          },
        },
      },
    });

    // 4. Group Operations Grid
    const opsContainer = document.getElementById('ceo-group-ops-grid');
    opsContainer.innerHTML = '';
    data.group_ops.forEach((bu) => {
      opsContainer.innerHTML += `
        <div class="bu-card">
          <div class="bu-name">${bu.business_unit}</div>
          <div class="bu-volume">${bu.volume.toLocaleString()}</div>
          <div class="bu-caption">KPI: ${bu.primary_kpi}</div>
          <div class="bu-caption" style="color: var(--teal-light);">Efficiency: ${bu.efficiency.toFixed(1)}% · Issues: ${bu.open_issues}</div>
        </div>
      `;
    });

    // 5. Management Signals
    const sigContainer = document.getElementById('ceo-signals-container');
    sigContainer.innerHTML = '';
    data.management_signals.forEach((sig) => {
      sigContainer.innerHTML += `
        <div class="signal-box">
          <i class="fa-solid fa-circle-info signal-icon" style="color: var(--gold-primary);"></i>
          <div>${sig.content}</div>
        </div>
      `;
    });

    // 6. Watch-outs
    const watchContainer = document.getElementById('ceo-watchouts-container');
    watchContainer.innerHTML = '';
    data.watch_outs.forEach((w) => {
      watchContainer.innerHTML += `
        <div class="signal-box alert">
          <i class="fa-solid fa-triangle-exclamation signal-icon" style="color: var(--coral-light);"></i>
          <div>${w.content}</div>
        </div>
      `;
    });

    // 7. Secondary Ops KPIs
    const opKpis = data.operational_metrics;
    document.getElementById('ceo-op-kpis').innerHTML = `
      ${renderMetricCard('Marketing Spend', opKpis.marketing_spend, null, 'fa-bullhorn')}
      ${renderMetricCard('Blended ROAS', opKpis.blended_roas, null, 'fa-arrow-trend-up')}
      ${renderMetricCard('CSAT Score', opKpis.csat, null, 'fa-smile')}
      ${renderMetricCard('QC Reject Rate', opKpis.qc_reject_rate, null, 'fa-shield-halved')}
    `;
  } catch (err) {
    console.error('Error loading CEO home:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 2: SALES COMMAND CENTER
// ---------------------------------------------------------------------------
async function loadSalesCommand(reqBody) {
  try {
    const res = await fetch('/api/sales-command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json();
    if (data.error) return;

    // Metrics
    const kpis = data.kpis;
    document.getElementById('sales-metrics-primary').innerHTML = `
      ${renderMetricCard('Net Sales', kpis.net.label, null, 'fa-money-bill-wave')}
      ${renderMetricCard('Gross Profit', kpis.profit.label, null, 'fa-coins')}
      ${renderMetricCard('Gross Margin', kpis.margin.label, null, 'fa-chart-pie')}
    `;
    document.getElementById('sales-metrics-secondary').innerHTML = `
      ${renderMetricCard('Gross Sales', kpis.gross.label, null, 'fa-file-invoice-dollar')}
      ${renderMetricCard('COGS', kpis.cogs.label, null, 'fa-boxes-packing')}
      ${renderMetricCard('Avg Discount', kpis.discount.label, null, 'fa-tag')}
      ${renderMetricCard('Refunds', kpis.refund.label, null, 'fa-rotate-left')}
    `;

    // Monthly Trajectory (Net Sales filled area + Gross Profit line)
    destroyChart('chart-sales-trajectory');
    const ctxTraj = document.getElementById('chart-sales-trajectory').getContext('2d');
    const trajMonths = data.monthly_trajectory.map((d) => d.month);
    const trajNet = data.monthly_trajectory.map((d) => d.net_sales);
    const trajProfit = data.monthly_trajectory.map((d) => d.gross_profit);

    state.charts['chart-sales-trajectory'] = new Chart(ctxTraj, {
      type: 'line',
      data: {
        labels: trajMonths,
        datasets: [
          {
            label: 'Net Sales (EGP)',
            data: trajNet,
            borderColor: COLORS.navyLight,
            backgroundColor: 'rgba(22, 56, 92, 0.35)',
            fill: true,
            borderWidth: 2,
            tension: 0.3,
          },
          {
            label: 'Gross Profit (EGP)',
            data: trajProfit,
            borderColor: COLORS.gold,
            backgroundColor: 'transparent',
            borderWidth: 3,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { callback: (v) => fmtEGP(v) } },
        },
      },
    });

    // Margin Trajectory
    destroyChart('chart-margin-trajectory');
    const ctxMargin = document.getElementById('chart-margin-trajectory').getContext('2d');
    state.charts['chart-margin-trajectory'] = new Chart(ctxMargin, {
      type: 'line',
      data: {
        labels: trajMonths,
        datasets: [
          {
            label: 'Gross Margin %',
            data: data.monthly_trajectory.map((d) => d.margin),
            borderColor: COLORS.tealLight,
            backgroundColor: 'rgba(46, 229, 157, 0.1)',
            fill: true,
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { ticks: { callback: (v) => fmtPct(v) }, grid: { color: 'rgba(255,255,255,0.06)' } },
        },
      },
    });

    // Discount vs Returns
    destroyChart('chart-discount-returns');
    const ctxDiscRet = document.getElementById('chart-discount-returns').getContext('2d');
    state.charts['chart-discount-returns'] = new Chart(ctxDiscRet, {
      type: 'bar',
      data: {
        labels: trajMonths,
        datasets: [
          {
            type: 'bar',
            label: 'Avg Discount %',
            data: data.monthly_trajectory.map((d) => d.discount),
            backgroundColor: 'rgba(196, 92, 38, 0.75)',
            yAxisID: 'y',
          },
          {
            type: 'line',
            label: 'Return Rate %',
            data: data.monthly_trajectory.map((d) => d.returns),
            borderColor: COLORS.tealLight,
            borderWidth: 2.5,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { position: 'left', ticks: { callback: (v) => fmtPct(v) } },
          y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: (v) => fmtPct(v) } },
        },
      },
    });

    // Seasonality Heatmap Table
    const heatTable = document.getElementById('table-seasonality');
    let heatHtml = `<thead><tr><th>Channel</th>${data.seasonality.months.map((m) => `<th>${m}</th>`).join('')}</tr></thead><tbody>`;
    data.seasonality.matrix.forEach((row) => {
      heatHtml += `<tr><td style="font-weight: 600; color: var(--gold-light);">${row.channel}</td>`;
      row.values.forEach((v) => {
        const bgAlpha = Math.min(0.85, Math.max(0.08, v / 5_000_000));
        heatHtml += `<td style="background: rgba(201, 162, 39, ${bgAlpha}); text-align: right;">${fmtEGP(v)}</td>`;
      });
      heatHtml += `</tr>`;
    });
    heatHtml += `</tbody>`;
    heatTable.innerHTML = heatHtml;

    // Discount Bands Bar Chart
    destroyChart('chart-discount-bands');
    const ctxBands = document.getElementById('chart-discount-bands').getContext('2d');
    state.charts['chart-discount-bands'] = new Chart(ctxBands, {
      type: 'bar',
      data: {
        labels: data.discount_bands.map((b) => b.bucket),
        datasets: [
          {
            label: 'Net Sales (EGP)',
            data: data.discount_bands.map((b) => b.net),
            backgroundColor: [COLORS.teal, COLORS.gold, COLORS.slate, COLORS.coral, COLORS.coralLight, '#991b1b'],
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { ticks: { callback: (v) => fmtEGP(v) } },
        },
      },
    });

    // Payment Methods Pie
    destroyChart('chart-payment-methods');
    const ctxPay = document.getElementById('chart-payment-methods').getContext('2d');
    state.charts['chart-payment-methods'] = new Chart(ctxPay, {
      type: 'doughnut',
      data: {
        labels: data.payment_methods.map((p) => p.method),
        datasets: [
          {
            data: data.payment_methods.map((p) => p.net),
            backgroundColor: [COLORS.gold, COLORS.teal, COLORS.navyLight, COLORS.coral, COLORS.slate],
            borderWidth: 2,
            borderColor: '#0a1628',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  } catch (err) {
    console.error('Error loading sales command:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 3: PRODUCTS & MIX
// ---------------------------------------------------------------------------
async function loadProducts(reqBody) {
  try {
    const res = await fetch('/api/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json();
    if (data.error) return;

    // 1. Family Contribution Bar Chart
    destroyChart('chart-family-contribution');
    const ctxFam = document.getElementById('chart-family-contribution').getContext('2d');
    state.charts['chart-family-contribution'] = new Chart(ctxFam, {
      type: 'bar',
      data: {
        labels: data.family_contribution.map((f) => f.family),
        datasets: [
          {
            label: 'Net Sales (EGP)',
            data: data.family_contribution.map((f) => f.net),
            backgroundColor: 'rgba(201, 162, 39, 0.85)',
            yAxisID: 'y',
            borderRadius: 6,
          },
          {
            type: 'line',
            label: 'Gross Margin %',
            data: data.family_contribution.map((f) => f.margin),
            borderColor: COLORS.tealLight,
            backgroundColor: COLORS.tealLight,
            borderWidth: 3,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { position: 'left', ticks: { callback: (v) => fmtEGP(v) } },
          y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: (v) => fmtPct(v) } },
        },
      },
    });

    // 2. Top 15 SKUs Horizontal Bar
    destroyChart('chart-top-skus');
    const ctxTop15 = document.getElementById('chart-top-skus').getContext('2d');
    state.charts['chart-top-skus'] = new Chart(ctxTop15, {
      type: 'bar',
      data: {
        labels: data.top15.map((s) => s.name.substring(0, 24)),
        datasets: [
          {
            axis: 'y',
            label: 'Net Sales (EGP)',
            data: data.top15.map((s) => s.net),
            backgroundColor: 'rgba(26, 122, 109, 0.85)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { callback: (v) => fmtEGP(v) } },
        },
      },
    });

    // 3. Pareto Analysis Top 25
    destroyChart('chart-pareto');
    const ctxPareto = document.getElementById('chart-pareto').getContext('2d');
    state.charts['chart-pareto'] = new Chart(ctxPareto, {
      type: 'bar',
      data: {
        labels: data.pareto25.map((s) => s.sku),
        datasets: [
          {
            type: 'bar',
            label: 'Net Sales (EGP)',
            data: data.pareto25.map((s) => s.net),
            backgroundColor: 'rgba(22, 56, 92, 0.9)',
            yAxisID: 'y',
          },
          {
            type: 'line',
            label: 'Cum. Share %',
            data: data.pareto25.map((s) => s.cum_share),
            borderColor: COLORS.gold,
            borderWidth: 2.5,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { position: 'left', ticks: { callback: (v) => fmtEGP(v) } },
          y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: (v) => fmtPct(v) }, min: 0, max: 1 },
        },
      },
    });

    // 4. SKU Table Top 40
    const tbody = document.querySelector('#table-sku-top40 tbody');
    tbody.innerHTML = '';
    data.sku_table.forEach((r) => {
      tbody.innerHTML += `
        <tr>
          <td style="font-family: monospace; color: var(--gold-light);">${r.sku}</td>
          <td>${r.name}</td>
          <td>${r.family}</td>
          <td style="font-weight: 600;">${r.net}</td>
          <td>${r.profit}</td>
          <td style="color: var(--teal-light);">${r.margin}</td>
          <td>${r.returns}</td>
          <td>${r.quality_returns}</td>
          <td>${r.discount}</td>
          <td>${r.cum_share}</td>
        </tr>
      `;
    });

    // 5. Return Reasons
    destroyChart('chart-return-reasons');
    const ctxRR = document.getElementById('chart-return-reasons').getContext('2d');
    state.charts['chart-return-reasons'] = new Chart(ctxRR, {
      type: 'bar',
      data: {
        labels: data.return_reasons.map((r) => r.reason),
        datasets: [
          {
            label: 'Refund Value (EGP)',
            data: data.return_reasons.map((r) => r.refund_val),
            backgroundColor: 'rgba(196, 92, 38, 0.85)',
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { ticks: { callback: (v) => fmtEGP(v) } },
        },
      },
    });
  } catch (err) {
    console.error('Error loading products:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 4: CUSTOMERS (RFM)
// ---------------------------------------------------------------------------
async function loadCustomers(reqBody) {
  try {
    const res = await fetch('/api/customers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json();
    if (data.error) return;

    // Metrics
    const kpis = data.kpis;
    document.getElementById('customers-kpis').innerHTML = `
      ${renderMetricCard('Active Customers', kpis.active_customers, null, 'fa-users')}
      ${renderMetricCard('Repeat Purchase Rate', kpis.repeat_rate, null, 'fa-repeat')}
      ${renderMetricCard('Avg Orders / Customer', kpis.avg_orders, null, 'fa-cart-shopping')}
      ${renderMetricCard('Top 10% Sales Share', kpis.top10_share, null, 'fa-gem')}
    `;

    // RFM Segments Bar Chart
    destroyChart('chart-rfm-segments');
    const ctxRfm = document.getElementById('chart-rfm-segments').getContext('2d');
    state.charts['chart-rfm-segments'] = new Chart(ctxRfm, {
      type: 'bar',
      data: {
        labels: data.rfm_segments.map((s) => s.segment),
        datasets: [
          {
            label: 'Net Sales (EGP)',
            data: data.rfm_segments.map((s) => s.sales),
            backgroundColor: [COLORS.tealLight, COLORS.gold, COLORS.slateLight, COLORS.coralLight, '#64748b'],
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { ticks: { callback: (v) => fmtEGP(v) } },
        },
      },
    });

    // Acquisition Channels
    destroyChart('chart-acquisition');
    const ctxAcq = document.getElementById('chart-acquisition').getContext('2d');
    state.charts['chart-acquisition'] = new Chart(ctxAcq, {
      type: 'bar',
      data: {
        labels: data.acquisition_channels.map((a) => a.channel),
        datasets: [
          {
            label: 'Sales (EGP)',
            data: data.acquisition_channels.map((a) => a.sales),
            backgroundColor: 'rgba(26, 122, 109, 0.8)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { ticks: { callback: (v) => fmtEGP(v) } } },
      },
    });

    // Age Bands
    destroyChart('chart-age-bands');
    const ctxAge = document.getElementById('chart-age-bands').getContext('2d');
    state.charts['chart-age-bands'] = new Chart(ctxAge, {
      type: 'bar',
      data: {
        labels: data.age_bands.map((a) => a.band),
        datasets: [
          {
            label: 'Sales (EGP)',
            data: data.age_bands.map((a) => a.sales),
            backgroundColor: 'rgba(74, 111, 165, 0.8)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { ticks: { callback: (v) => fmtEGP(v) } } },
      },
    });

    // Top Customers Table
    const tbody = document.querySelector('#table-top-customers tbody');
    tbody.innerHTML = '';
    data.top_customers.forEach((c) => {
      let badgeCls = 'badge-promising';
      if (c.segment === 'Champions') badgeCls = 'badge-champion';
      else if (c.segment === 'Loyal') badgeCls = 'badge-loyal';
      else if (c.segment === 'At risk') badgeCls = 'badge-at-risk';
      else if (c.segment === 'Hibernating') badgeCls = 'badge-hibernating';

      tbody.innerHTML += `
        <tr>
          <td style="font-family: monospace; color: var(--gold-light);">${c.customer_id}</td>
          <td>${c.customer_type}</td>
          <td>${c.governorate}</td>
          <td>${c.recency_days} days</td>
          <td>${c.orders}</td>
          <td style="font-weight: 600;">${c.net_egp}</td>
          <td><span class="badge-tag ${badgeCls}">${c.segment}</span></td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error loading customers:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 5: CHANNELS & MARKETS
// ---------------------------------------------------------------------------
async function loadChannels(reqBody) {
  try {
    const res = await fetch('/api/channels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json();
    if (data.error) return;

    // Channel x Location Table
    const tbody = document.querySelector('#table-channel-location tbody');
    tbody.innerHTML = '';
    data.channel_location_table.forEach((r) => {
      tbody.innerHTML += `
        <tr>
          <td style="font-weight: 600; color: var(--gold-light);">${r.channel}</td>
          <td>${r.location}</td>
          <td>${r.net}</td>
          <td>${r.profit}</td>
          <td style="color: var(--teal-light); font-weight: 600;">${r.margin}</td>
          <td>${r.aov}</td>
          <td>${r.units}</td>
          <td>${r.returns}</td>
          <td>${r.discount}</td>
        </tr>
      `;
    });

    // Monthly Channel Mix (Stacked Bar)
    destroyChart('chart-channel-mix');
    const ctxMix = document.getElementById('chart-channel-mix').getContext('2d');
    const mixColors = [COLORS.navyLight, COLORS.gold, COLORS.teal, COLORS.coral];
    const datasets = data.mix_series.channels.map((ch, idx) => ({
      label: ch,
      data: data.mix_series.data[ch],
      backgroundColor: mixColors[idx % mixColors.length],
      stack: 'channels',
    }));

    state.charts['chart-channel-mix'] = new Chart(ctxMix, {
      type: 'bar',
      data: {
        labels: data.mix_series.months,
        datasets: datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true },
          y: { stacked: true, ticks: { callback: (v) => fmtEGP(v) } },
        },
      },
    });

    // Demand by Governorate
    destroyChart('chart-governorates');
    const ctxGov = document.getElementById('chart-governorates').getContext('2d');
    state.charts['chart-governorates'] = new Chart(ctxGov, {
      type: 'bar',
      data: {
        labels: data.governorates.map((g) => g.governorate),
        datasets: [
          {
            label: 'Net Sales (EGP)',
            data: data.governorates.map((g) => g.net),
            backgroundColor: 'rgba(201, 162, 39, 0.85)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { ticks: { callback: (v) => fmtEGP(v) } } },
      },
    });

    // Digital Funnel
    if (data.digital_funnel) {
      document.getElementById('digital-funnel-card').style.display = 'block';
      const df = data.digital_funnel;
      document.getElementById('digital-kpis').innerHTML = `
        ${renderMetricCard('Online Sessions', df.sessions, null, 'fa-users-line')}
        ${renderMetricCard('Conversion Rate', df.conversion, null, 'fa-arrow-progress')}
        ${renderMetricCard('Add to Cart', df.add_to_cart, null, 'fa-cart-plus')}
        ${renderMetricCard('Avg Page Load', df.avg_load, null, 'fa-stopwatch')}
      `;

      destroyChart('chart-web-conv');
      const ctxWeb = document.getElementById('chart-web-conv').getContext('2d');
      state.charts['chart-web-conv'] = new Chart(ctxWeb, {
        type: 'line',
        data: {
          labels: df.daily_trend.map((d) => d.date),
          datasets: [
            {
              label: 'Daily Conversion Rate',
              data: df.daily_trend.map((d) => d.conversion_rate),
              borderColor: COLORS.tealLight,
              borderWidth: 1.5,
              pointRadius: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { display: false },
            y: { ticks: { callback: (v) => fmtPct(v) } },
          },
        },
      });
    } else {
      document.getElementById('digital-funnel-card').style.display = 'none';
    }
  } catch (err) {
    console.error('Error loading channels:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 6: OPERATIONS PULSE
// ---------------------------------------------------------------------------
async function loadOperations(reqBody) {
  try {
    const res = await fetch('/api/operations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json();

    // Top KPIs
    const kpis = data.kpis;
    document.getElementById('ops-top-kpis').innerHTML = `
      ${renderMetricCard('Closing Stock', kpis.closing_stock, null, 'fa-warehouse')}
      ${renderMetricCard('Stockout Days', kpis.stockouts, null, 'fa-boxes-packing')}
      ${renderMetricCard('Factory Efficiency', kpis.factory_efficiency, null, 'fa-gauge-high')}
      ${renderMetricCard('Avg Production Delay', kpis.avg_delay, null, 'fa-clock')}
      ${renderMetricCard('Cost of Quality Loss', kpis.quality_loss, null, 'fa-triangle-exclamation')}
    `;

    // Days of Cover Histogram
    destroyChart('chart-cover-hist');
    const ctxHist = document.getElementById('chart-cover-hist').getContext('2d');
    state.charts['chart-cover-hist'] = new Chart(ctxHist, {
      type: 'bar',
      data: {
        labels: data.cover_histogram.map((b) => b.bin + ' Days'),
        datasets: [
          {
            label: 'SKU Count',
            data: data.cover_histogram.map((b) => b.count),
            backgroundColor: [COLORS.coralLight, COLORS.coral, COLORS.gold, COLORS.teal, COLORS.slate, '#38bdf8', '#818cf8'],
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });

    // Low Cover SKUs Table
    const tbodyLow = document.querySelector('#table-low-cover tbody');
    tbodyLow.innerHTML = '';
    data.low_cover_skus.forEach((s) => {
      tbodyLow.innerHTML += `
        <tr>
          <td>${s.location}</td>
          <td style="font-family: monospace; color: var(--gold-light);">${s.sku}</td>
          <td>${s.name}</td>
          <td>${s.stock}</td>
          <td style="color: var(--coral-light); font-weight: 700;">${s.days_cover}</td>
          <td>${s.stockout_days}</td>
        </tr>
      `;
    });

    // Quality Defect Pareto
    destroyChart('chart-defects');
    const ctxDefects = document.getElementById('chart-defects').getContext('2d');
    state.charts['chart-defects'] = new Chart(ctxDefects, {
      type: 'bar',
      data: {
        labels: data.defect_pareto.map((d) => d.defect),
        datasets: [
          {
            label: 'Estimated Loss (EGP)',
            data: data.defect_pareto.map((d) => d.loss),
            backgroundColor: 'rgba(196, 92, 38, 0.85)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { ticks: { callback: (v) => fmtEGP(v) } } },
      },
    });

    // Production Bottlenecks
    destroyChart('chart-bottlenecks');
    const ctxBottlenecks = document.getElementById('chart-bottlenecks').getContext('2d');
    state.charts['chart-bottlenecks'] = new Chart(ctxBottlenecks, {
      type: 'bar',
      data: {
        labels: data.production_bottlenecks.map((b) => b.bottleneck),
        datasets: [
          {
            label: 'Orders Impacted',
            data: data.production_bottlenecks.map((b) => b.orders),
            backgroundColor: 'rgba(74, 111, 165, 0.85)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });

    // Marketing Platform Table
    const tbodyMkt = document.querySelector('#table-marketing tbody');
    tbodyMkt.innerHTML = '';
    data.marketing_platforms.forEach((m) => {
      tbodyMkt.innerHTML += `
        <tr>
          <td style="font-weight: 600; color: var(--gold-light);">${m.platform}</td>
          <td>${m.spend}</td>
          <td>${m.revenue}</td>
          <td>${m.orders}</td>
          <td style="color: var(--teal-light); font-weight: 700;">${m.roas}</td>
        </tr>
      `;
    });

    // Customer Service Summary
    if (data.service_summary) {
      const svc = data.service_summary;
      document.getElementById('service-kpis').innerHTML = `
        ${renderMetricCard('Total Tickets', svc.tickets, null, 'fa-ticket')}
        ${renderMetricCard('Resolved Rate', svc.resolved, null, 'fa-check')}
        ${renderMetricCard('Avg CSAT', svc.csat, null, 'fa-star')}
      `;

      destroyChart('chart-service-tickets');
      const ctxSvc = document.getElementById('chart-service-tickets').getContext('2d');
      state.charts['chart-service-tickets'] = new Chart(ctxSvc, {
        type: 'bar',
        data: {
          labels: svc.ticket_mix.map((t) => t.issue),
          datasets: [
            {
              label: 'Tickets',
              data: svc.ticket_mix.map((t) => t.tickets),
              backgroundColor: 'rgba(26, 122, 109, 0.8)',
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
        },
      });
    }
  } catch (err) {
    console.error('Error loading operations:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 7: DATA EXPLORER
// ---------------------------------------------------------------------------
function setupExplorer() {
  const searchInput = document.getElementById('explorer-search');
  let debounceTimeout = null;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      state.explorer.search = e.target.value;
      state.explorer.page = 1;
      loadExplorerData();
    }, 300);
  });

  document.getElementById('btn-prev-page').addEventListener('click', () => {
    if (state.explorer.page > 1) {
      state.explorer.page--;
      loadExplorerData();
    }
  });

  document.getElementById('btn-next-page').addEventListener('click', () => {
    if (state.explorer.page < state.explorer.totalPages) {
      state.explorer.page++;
      loadExplorerData();
    }
  });

  document.getElementById('btn-export-csv').addEventListener('click', async () => {
    const btn = document.getElementById('btn-export-csv');
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Preparing CSV...`;
    btn.disabled = true;

    try {
      const res = await fetch('/api/export-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.filters),
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'elsharnouby_sales_filtered.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export CSV: ' + err.message);
    } finally {
      btn.innerHTML = `<i class="fa-solid fa-file-csv"></i> Download Filtered CSV`;
      btn.disabled = false;
    }
  });
}

async function loadExplorerData() {
  const tbody = document.getElementById('tbody-explorer');
  const thead = document.getElementById('thead-explorer');
  tbody.innerHTML = `<tr><td colspan="15" class="spinner-container"><div class="spinner"></div> Loading filtered transactions...</td></tr>`;

  try {
    const payload = {
      ...state.filters,
      search: state.explorer.search,
      page: state.explorer.page,
      page_size: state.explorer.pageSize,
    };

    const res = await fetch('/api/explorer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    state.explorer.totalPages = data.total_pages;

    // Header
    thead.innerHTML = `<tr>${data.columns.map((c) => `<th>${c.replace(/_/g, ' ')}</th>`).join('')}</tr>`;

    // Rows
    if (data.rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${data.columns.length}" style="text-align: center; padding: 2rem; color: var(--text-muted);">No records found.</td></tr>`;
    } else {
      tbody.innerHTML = data.rows
        .map((row) => `<tr>${data.columns.map((c) => `<td>${row[c]}</td>`).join('')}</tr>`)
        .join('');
    }

    // Pagination info
    document.getElementById('explorer-row-count').textContent = `${data.total_records.toLocaleString()} rows`;
    document.getElementById('explorer-page-num').textContent = `${data.page} / ${data.total_pages}`;
    document.getElementById('btn-prev-page').disabled = data.page <= 1;
    document.getElementById('btn-next-page').disabled = data.page >= data.total_pages;
  } catch (err) {
    console.error('Error loading explorer:', err);
  }
}

// ---------------------------------------------------------------------------
// VIEW 8: EXECUTIVE AI CHATBOT
// ---------------------------------------------------------------------------
function setupChat() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const thread = document.getElementById('chat-thread');

  // Scope toggle
  document.getElementById('btn-scope-filtered').addEventListener('click', () => {
    state.chatScope = 'Active Filtered Slice';
    document.getElementById('btn-scope-filtered').classList.add('active');
    document.getElementById('btn-scope-all').classList.remove('active');
  });

  document.getElementById('btn-scope-all').addEventListener('click', () => {
    state.chatScope = 'Full Historical Database';
    document.getElementById('btn-scope-all').classList.add('active');
    document.getElementById('btn-scope-filtered').classList.remove('active');
  });

  // Clear Chat
  document.getElementById('btn-clear-chat').addEventListener('click', () => {
    state.chatHistory = [];
    thread.innerHTML = `
      <div class="chat-bubble assistant">
        <h3>◈ مرحباً بكم في المساعد الاستراتيجي والتحليلي لمجموعة الشرنوبي</h3>
        <p>تم تفريغ المحادثة. يمكنك الآن طرح استفسارات جديدة مرتبطة بالمبيعات، سلاسل الإمداد، الجودة، أو ربحية الفروع وقنوات التوزيع.</p>
      </div>
    `;
  });

  // Quick prompt buttons
  document.querySelectorAll('.quick-prompt-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const q = btn.getAttribute('data-prompt');
      input.value = q;
      form.dispatchEvent(new Event('submit'));
    });
  });

  // Form submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = input.value.trim();
    if (!prompt) return;

    input.value = '';
    const submitBtn = document.getElementById('btn-submit-chat');
    submitBtn.disabled = true;

    // Render User Message
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = prompt;
    thread.appendChild(userBubble);

    // Render Assistant Loading Bubble
    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'chat-bubble assistant';
    assistantBubble.innerHTML = `<div class="spinner-container" style="padding: 0.5rem;"><div class="spinner"></div> جاري تحليل بيانات المؤسسة وإعداد التقرير التنفيذي...</div>`;
    thread.appendChild(assistantBubble);
    thread.scrollTop = thread.scrollHeight;

    // Append to local history
    state.chatHistory.push({ role: 'user', content: prompt });

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: prompt,
          data_scope: state.chatScope,
          filters: state.filters,
          history: state.chatHistory,
        }),
      });
      const data = await res.json();

      // Render markdown response
      assistantBubble.innerHTML = marked.parse(data.answer);
      state.chatHistory.push({ role: 'assistant', content: data.answer });
    } catch (err) {
      assistantBubble.innerHTML = `<p style="color: var(--coral-light);">⚠️ عذراً، حدث خطأ أثناء الاتصال بالخادم: ${err.message}</p>`;
    } finally {
      submitBtn.disabled = false;
      thread.scrollTop = thread.scrollHeight;
    }
  });
}

// Run on page load
document.addEventListener('DOMContentLoaded', initApp);
