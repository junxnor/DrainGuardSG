const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (value, digits=1) => value == null || value === '' ? '-' : Number(value).toFixed(digits);

let snapshot = null;
const stateFilter = $('#stateFilter');
const districtFilter = $('#districtFilter');
const pageTitles = {overview:'Overview', rainfall:'Rainfall Monitoring', water:'Water-Level Monitoring'};
const officialPages = {
  Selangor: {
    rainfall:'https://publicinfobanjir.water.gov.my/hujan/data-hujan/?state=SEL&type=NEGERI&lang=en',
    water:'https://publicinfobanjir.water.gov.my/aras-air/data-paras-air/?state=SEL&type=NEGERI&lang=en'
  },
  'Kuala Lumpur': {
    rainfall:'https://publicinfobanjir.water.gov.my/hujan/data-hujan/?state=WLH&type=NEGERI&lang=en',
    water:'https://publicinfobanjir.water.gov.my/aras-air/data-paras-air/?state=WLH&lang=en'
  },
  Putrajaya: {
    rainfall:'https://publicinfobanjir.water.gov.my/hujan/data-hujan/?state=PTJ&type=NEGERI&lang=en',
    water:'https://publicinfobanjir.water.gov.my/aras-air/data-paras-air/?state=PTJ&lang=en'
  }
};

function setOptions(select, values, firstLabel, selected='') {
  select.innerHTML = `<option value="">${firstLabel}</option>` + values.map(value => `<option value="${esc(value)}">${esc(value)}</option>`).join('');
  if (values.includes(selected)) select.value = selected;
}

async function refresh(resetDistrict=false) {
  if (resetDistrict) districtFilter.value = '';
  const query = new URLSearchParams();
  if (stateFilter.value) query.set('state', stateFilter.value);
  if (districtFilter.value) query.set('district', districtFilter.value);
  const response = await fetch('/api/demo-data?' + query.toString());
  if (!response.ok) throw new Error('Could not load the demo history.');
  snapshot = await response.json();
  if (stateFilter.options.length <= 1) setOptions(stateFilter, snapshot.states, 'All states', stateFilter.value);
  setOptions(districtFilter, snapshot.districts, 'ALL', districtFilter.value);
  render(snapshot);
}

function metric(label, value, hint, icon) {
  return `<article class="metric"><div class="metric-top">${label}<span class="metric-icon">${icon}</span></div><strong>${value}</strong><small>${hint}</small></article>`;
}

function render(data) {
  const s = data.summary, o = data.outlook, m = data.model;
  $('#metrics').innerHTML = [
    metric('Rainfall stations', s.rainfall_stations, 'selected area', 'R'),
    metric('Water-level stations', s.water_level_stations, 'selected area', 'W'),
    metric('Water-level Warning (below Danger)', s.at_warning_below_danger, 'Warning threshold reached; Danger excluded', '!'),
    metric('Water-level Danger or higher', s.at_danger, 'Danger threshold reached', 'D'),
  ].join('');

  const badge = $('#riskBadge');
  badge.textContent = o.indicator;
  badge.className = 'risk-badge ' + o.label.toLowerCase();
  $('#outlookMessage').textContent=o.message;
  $('#outlookMessage').className='outlook-message '+o.label.toLowerCase();
  $('#rainForecast').textContent = fmt(o.max_predicted_rain_mm);
  $('#waterStage').textContent = fmt(o.max_water_level_m, 2) + ' m';
  $('#dangerThreshold').textContent = o.threshold_for_max_level_m == null ? 'no threshold available' : `highest recorded danger threshold ${fmt(o.threshold_for_max_level_m, 2)} m`;
  $('#scoreText').textContent = `${o.score} / 100`;
  $('#scoreBar').style.width = `${o.score}%`;
  $('#outlookBasis').textContent = o.basis;
  $('#guidance').innerHTML = o.guidance.map(item => `<li>${esc(item)}</li>`).join('');
  const stationAlerts=data.water_level_alerts||[];
  $('#stationAlerts').innerHTML = stationAlerts.length
    ? `<h4>Water-level stations at Alert threshold or higher (${stationAlerts.length})</h4><ul>${stationAlerts.map(a=>`<li><span class="stage ${a.status.toLowerCase()}">${a.status}</span> <b>${esc(a.station_name)}</b> - ${esc(a.district)}, ${esc(a.state)}: ${fmt(a.water_level_m,2)} m; threshold ${fmt(a.threshold_m,2)} m</li>`).join('')}</ul>`
    : '<h4>Water-level station thresholds</h4><p>No selected station is at or above its Alert threshold in this historical demo snapshot.</p>';
  const linkedStates = stateFilter.value ? [stateFilter.value] : Object.keys(officialPages);
  $('#officialLinks').innerHTML = `<h4>Official Public InfoBanjir information</h4><div class="official-link-list">${linkedStates.flatMap(area=>[
    `<a href="${esc(officialPages[area].rainfall)}" target="_blank" rel="noopener">${esc(area)} rainfall</a>`,
    `<a href="${esc(officialPages[area].water)}" target="_blank" rel="noopener">${esc(area)} water level</a>`
  ]).join('')}</div>`;
  $('#modelInfo').textContent = `Random Forest trained on five-day rainfall windows from ${m.stations} stations. Training inputs: 6-10 Nov 2026; target: 11 Nov. The current outlook uses 7-11 Nov to estimate 12 Nov.`;
  $('#modelMetric').textContent = `Station holdout review: MAE ${fmt(m.holdout_mae_mm)} mm; RMSE ${fmt(m.holdout_rmse_mm)} mm; R-squared ${fmt(m.holdout_r2, 3)}.`;

  $('#rainCount').textContent = `${data.rainfall.length} stations`;
  $('#rainRows').innerHTML = data.rainfall.map(r => `<tr>
    <td><b>${esc(r.station_name)}</b><small class="muted">${esc(r.station_id)}</small></td><td>${esc(r.district)}</td>
    ${r.daily_history_mm.map(v => `<td>${fmt(v)}</td>`).join('')}
    <td>${fmt(r.rainfall_from_midnight_mm)}</td><td>${fmt(r.rainfall_1h_mm)}</td><td>${rainClass(r.rainfall_1h_mm)}</td><td class="forecast-cell">${fmt(r.predicted_next_day_mm)}</td>
  </tr>`).join('') || '<tr><td colspan="11" class="empty-row">No rainfall stations for this filter.</td></tr>';

  $('#waterCount').textContent = `${data.water_levels.length} stations`;
  $('#waterRows').innerHTML = data.water_levels.map(r => {
    const level = r.water_level_m;
    const status = level == null ? 'No level' : r.danger_m != null && level >= r.danger_m ? 'Danger' : r.warning_m != null && level >= r.warning_m ? 'Warning' : r.alert_m != null && level >= r.alert_m ? 'Alert' : 'Normal';
    return `<tr><td><b>${esc(r.station_name)}</b><small class="muted">${esc(r.station_id)}</small></td><td>${esc(r.district)}</td>
      <td>${esc(r.main_basin)}<small class="muted">${esc(r.sub_river_basin)}</small></td><td>${esc(r.last_updated)}</td><td>${fmt(level,2)}</td>
      <td>${fmt(r.normal_m,2)}</td><td>${fmt(r.alert_m,2)}</td><td>${fmt(r.warning_m,2)}</td><td>${fmt(r.danger_m,2)}</td><td><span class="stage ${status.toLowerCase().replace(' ','-')}">${status}</span></td></tr>`;
  }).join('') || '<tr><td colspan="10" class="empty-row">No water-level stations for this filter.</td></tr>';
}

function rainClass(value) {
  if (value == null || value <= 0) return '<span class="rain-class none">No rain</span>';
  if (value <= 10) return '<span class="rain-class light">Light</span>';
  if (value <= 30) return '<span class="rain-class moderate">Moderate</span>';
  if (value <= 60) return '<span class="rain-class heavy">Heavy</span>';
  return '<span class="rain-class very-heavy">Very Heavy</span>';
}

function showPage(page, pushHistory=false) {
  if (!pageTitles[page]) page='overview';
  document.querySelectorAll('.page-section').forEach(section => section.classList.toggle('active-page', section.id===page));
  document.querySelectorAll('.sidebar nav a').forEach(link => {
    const active=link.dataset.page===page;
    link.classList.toggle('active',active);
    if(active) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  });
  $('#pageTitle').textContent=pageTitles[page];
  $('#pageCrumb').textContent=pageTitles[page].toUpperCase();
  if(pushHistory) history.pushState({page},'',`#${page}`);
  document.querySelector('.sidebar').classList.remove('open');
  window.scrollTo({top:0,behavior:'smooth'});
}

stateFilter.addEventListener('change', () => refresh(true).catch(showError));
districtFilter.addEventListener('change', () => refresh().catch(showError));
document.querySelectorAll('.sidebar nav a').forEach(link => link.addEventListener('click', event => {
  event.preventDefault();
  showPage(link.dataset.page,true);
}));
document.querySelector('.brand').addEventListener('click', event => {
  event.preventDefault();
  showPage('overview',true);
});
window.addEventListener('popstate', () => showPage(location.hash.slice(1)));
$('#mobileMenu').addEventListener('click', () => document.querySelector('.sidebar').classList.toggle('open'));

function showError(error) {
  $('#metrics').innerHTML = `<div class="notice">${esc(error.message)}</div>`;
}

showPage(location.hash.slice(1) || 'overview');
refresh().catch(showError);
