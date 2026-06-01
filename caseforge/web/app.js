const briefForm = document.getElementById('brief-form');
const projectBrief = document.getElementById('project-brief');
const audience = document.getElementById('audience');
const mode = document.getElementById('mode');
const goal = document.getElementById('goal');
const preset = document.getElementById('preset');
const provider = document.getElementById('provider');
const briefMeta = document.getElementById('brief-meta');
const statusLine = document.getElementById('status');
const transportChip = document.getElementById('transport-chip');
const markdownChip = document.getElementById('markdown-chip');
const sourceChip = document.getElementById('source-chip');
const markdownPath = document.getElementById('markdown-path');
const dossierTitle = document.getElementById('dossier-title');
const dossierSummary = document.getElementById('dossier-summary');
const insightRow = document.getElementById('insight-row');
const sectionGrid = document.getElementById('section-grid');
const sectionTemplate = document.getElementById('section-template');
const previewButton = document.getElementById('preview-button');
const forgeButton = document.getElementById('forge-button');
const sampleButton = document.getElementById('sample-button');
const copyBriefButton = document.getElementById('copy-brief-button');
const copyMarkdownButton = document.getElementById('copy-markdown-button');
const readinessCard = document.getElementById('readiness-card');
const readinessTitle = document.getElementById('readiness-title');
const readinessCopy = document.getElementById('readiness-copy');
const refreshRecentButton = document.getElementById('refresh-recent-button');
const recentList = document.getElementById('recent-list');
const compareSelectionLabel = document.getElementById('compare-selection');
const compareButton = document.getElementById('compare-button');
const clearCompareButton = document.getElementById('clear-compare-button');
const compareResult = document.getElementById('compare-result');
const alertPanel = document.getElementById('alert-panel');
const scoreValue = document.getElementById('score-value');
const recommendationValue = document.getElementById('recommendation-value');
const providerValue = document.getElementById('provider-value');
const providerMessage = document.getElementById('provider-message');
const artifactValue = document.getElementById('artifact-value');
const artifactMessage = document.getElementById('artifact-message');
const exportMarkdownPath = document.getElementById('export-markdown-path');
const exportJsonPath = document.getElementById('export-json-path');
const exportSummaryPath = document.getElementById('export-summary-path');
const openMarkdownLink = document.getElementById('open-markdown-link');
let recentDossiers = [];
const compareSelection = new Set();
const formStateKey = 'caseforge:formState';

const presetBriefs = {
  'release-planner': {
    brief:
      'Build a release readiness planner that turns incident notes, service metrics, owner comments, and follow-up tasks into an action plan with risks, owners, validation checks, and next-step recommendations for an engineering lead.',
    audience: 'Engineering lead',
    mode: 'Workflow product',
    goal: 'Drive implementation clarity',
    preset: 'full-stack',
    provider: 'deterministic',
  },
  'ai-copilot': {
    brief:
      'Build an AI operations copilot that turns incident notes, service metrics, and follow-up tasks into a release-ready action plan.',
    audience: 'Technical stakeholders',
    mode: 'AI assistant',
    goal: 'Emphasize AI decisioning',
    preset: 'ml',
    provider: 'deterministic',
  },
  'ops-brief': {
    brief:
      'Create an operations copilot that summarizes incidents, drafts a retrospective, proposes follow-up actions, and keeps the team aligned after every escalation.',
    audience: 'Engineering lead',
    mode: 'Workflow product',
    goal: 'Drive implementation clarity',
    preset: 'full-stack',
    provider: 'deterministic',
  },
  'study-lens': {
    brief:
      'Design a study companion that turns lecture notes, slides, and saved links into quizzes, revision plans, and memory-friendly summaries for exam prep.',
    audience: 'Internal team',
    mode: 'Study companion',
    goal: 'Strengthen product framing',
    preset: 'product',
    provider: 'deterministic',
  },
  'founder-note': {
    brief:
      'Ship a founder note-taking app that converts messy voice captures into weekly priorities, investor updates, and a clean decision log.',
    audience: 'Startup founder',
    mode: 'Developer tool',
    goal: 'Emphasize shipping discipline',
    preset: 'founder',
    provider: 'deterministic',
  },
};

function bootstrap() {
  const savedState = readStoredJson(formStateKey);
  const savedBrief = readStoredValue('caseforge:lastBrief');
  if (savedState?.brief) {
    applyPayloadToForm(savedState);
  } else if (savedBrief) {
    projectBrief.value = savedBrief;
  } else {
    loadPreset('release-planner', { persist: false });
  }

  updateMeta();
  renderDossier(buildLocalDossier(buildPayload()), { source: 'local sample' });
  setStatus('Release planner sample loaded. Preview without saving, then forge a run to create export files.', 'pending');
  setAlert(
    'Start with the release planner sample.',
    'Preview uses the backend without saving. Forge blueprint creates Markdown, JSON, and summary exports that can be compared against later runs.',
    'info',
  );
  renderCompareSelectionState();
  refreshRecentDossiers();
  document.documentElement.classList.add('ready');
}

function buildPayload() {
  return {
    brief: projectBrief.value.trim(),
    audience: audience.value,
    mode: mode.value,
    goal: goal.value,
    preset: preset.value,
    provider: provider.value,
  };
}

function loadPreset(name, options = { persist: true }) {
  const next = presetBriefs[name];
  if (!next) return;
  applyPayloadToForm(next);
  updateMeta();
  if (options.persist) {
    writeFormState();
  }
}

function applyPayloadToForm(payload) {
  projectBrief.value = payload.brief || '';
  setSelectValue(audience, payload.audience);
  setSelectValue(mode, payload.mode);
  setSelectValue(goal, payload.goal);
  setSelectValue(preset, payload.preset);
  setSelectValue(provider, payload.provider);
}

function setSelectValue(selectElement, value) {
  if (!value) {
    return;
  }
  const hasOption = Array.from(selectElement.options).some((option) => option.value === value);
  if (hasOption) {
    selectElement.value = value;
  }
}

function updateMeta() {
  const words = tokenize(projectBrief.value).length;
  const state = getBriefReadiness(words);
  briefMeta.textContent = `${words} word${words === 1 ? '' : 's'} - ${state.meta}.`;
  readinessCard.dataset.state = state.kind;
  readinessTitle.textContent = state.title;
  readinessCopy.textContent = state.copy;
}

function tokenize(text) {
  return text.trim().split(/\s+/).filter(Boolean);
}

function getBriefReadiness(words) {
  if (words < 8) {
    return {
      kind: 'low',
      title: 'Too thin for a useful blueprint',
      meta: 'add the user, input, and expected artifact',
      copy: 'A one-line idea can be previewed, but persisted blueprints work better with at least a user, input source, output artifact, and review constraint.',
    };
  }

  if (words < 20) {
    return {
      kind: 'medium',
      title: 'Usable first pass',
      meta: 'ready, but more context will improve sections',
      copy: 'This is enough for a first pass. Add success criteria, constraints, or review audience if you want a stronger implementation path.',
    };
  }

  return {
    kind: 'high',
    title: 'Ready for a serious pass',
    meta: 'ready for generation',
    copy: 'The brief has enough context for problem framing, architecture notes, tradeoffs, and a delivery path.',
  };
}

function readStoredValue(key) {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStoredValue(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    return false;
  }
  return true;
}

function readStoredJson(key) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeFormState() {
  try {
    window.localStorage.setItem(formStateKey, JSON.stringify(buildPayload()));
  } catch {
    return false;
  }
  return true;
}

function normalizeDossier(payload, fallbackMeta = {}) {
  const raw = payload?.title || payload?.summary || payload?.sections ? payload : (payload?.dossier ?? payload ?? {});
  const dossierRecord = payload?.dossier ?? raw?.dossier ?? {};
  const evaluator = dossierRecord?.evaluator ?? raw?.evaluator ?? {};
  const markdownPathValue =
    payload?.markdownPath ??
    payload?.markdown_path ??
    raw?.markdownPath ??
    raw?.markdown_path ??
    fallbackMeta.markdownPath ??
    '';
  const jsonPathValue =
    payload?.jsonPath ??
    payload?.json_path ??
    raw?.jsonPath ??
    raw?.json_path ??
    fallbackMeta.jsonPath ??
    '';
  const summaryPathValue =
    payload?.summaryPath ??
    payload?.summary_path ??
    raw?.summaryPath ??
    raw?.summary_path ??
    fallbackMeta.summaryPath ??
    '';

  const sections = Array.isArray(raw.sections) && raw.sections.length
    ? raw.sections.map((section, index) => ({
        label: section.label || `Section ${index + 1}`,
        title: section.title || section.label || `Section ${index + 1}`,
        body: section.body || section.content || '',
      }))
    : [];

  return {
    title: raw.title || 'Untitled blueprint',
    summary: raw.summary || 'No summary returned by the backend.',
    insights: Array.isArray(raw.insights) ? raw.insights : [],
    sections,
    markdownPath: markdownPathValue,
    jsonPath: jsonPathValue,
    summaryPath: summaryPathValue,
    persisted: payload?.persisted ?? raw?.persisted ?? Boolean(markdownPathValue),
    preview: payload?.preview ?? raw?.preview ?? false,
    providerStatus: payload?.providerStatus ?? payload?.provider_status ?? raw?.providerStatus ?? raw?.provider_status ?? 'deterministic',
    provider: payload?.provider ?? raw?.provider ?? raw?.brief?.provider ?? 'deterministic',
    providerMessage: payload?.providerMessage ?? payload?.provider_message ?? raw?.providerMessage ?? raw?.provider_message ?? '',
    score: evaluator?.overall_score ?? payload?.score ?? raw?.score ?? null,
    recommendation: evaluator?.recommendation ?? payload?.recommendation ?? raw?.recommendation ?? '',
  };
}

function renderDossier(payload, meta = {}) {
  const dossier = normalizeDossier(payload, meta);
  dossierTitle.textContent = dossier.title;
  dossierSummary.textContent = dossier.summary;
  markdownPath.textContent = dossier.markdownPath || 'No export path yet.';
  exportMarkdownPath.textContent = dossier.markdownPath || 'Not saved yet';
  exportJsonPath.textContent = dossier.jsonPath || 'Not saved yet';
  exportSummaryPath.textContent = dossier.summaryPath || 'Not saved yet';
  if (openMarkdownLink) {
    const canOpenMarkdown = dossier.markdownPath && dossier.persisted;
    openMarkdownLink.classList.toggle('is-disabled', !canOpenMarkdown);
    openMarkdownLink.toggleAttribute('aria-disabled', !canOpenMarkdown);
    if (canOpenMarkdown) {
      openMarkdownLink.href = `/${dossier.markdownPath.replace(/\\/g, '/')}`;
      openMarkdownLink.setAttribute('target', '_blank');
      openMarkdownLink.setAttribute('rel', 'noopener');
    } else {
      openMarkdownLink.removeAttribute('href');
      openMarkdownLink.removeAttribute('target');
      openMarkdownLink.removeAttribute('rel');
    }
  }
  markdownChip.textContent = dossier.persisted ? 'Markdown: ready' : 'Markdown: preview only';
  sourceChip.textContent = `Source: ${meta.source || 'backend'}`;
  transportChip.textContent = meta.source === 'local sample'
    ? 'Backend: sample seed'
    : `Backend: ${dossier.provider} (${dossier.providerStatus})`;
  scoreValue.textContent = dossier.score === null ? 'Preview' : `${dossier.score}/100`;
  recommendationValue.textContent = dossier.recommendation || (dossier.persisted ? 'Saved run' : 'No backend score yet');
  providerValue.textContent = `${capitalize(dossier.provider)} (${dossier.providerStatus})`;
  providerMessage.textContent = dossier.providerMessage || 'Deterministic path remains the default review path.';
  artifactValue.textContent = dossier.persisted ? 'Saved' : 'Preview';
  artifactMessage.textContent = dossier.persisted
    ? 'Markdown, JSON, and summary paths are available below.'
    : 'Persist the run to create export files.';

  insightRow.innerHTML = '';
  const insights = dossier.insights.length
    ? dossier.insights
    : ['Keep the first release narrow.', 'Make the tradeoffs explicit.', 'Keep the workflow repeatable.'];
  insights.slice(0, 4).forEach((insight) => {
    const node = document.createElement('span');
    node.className = 'pill';
    node.textContent = insight;
    insightRow.appendChild(node);
  });

  sectionGrid.innerHTML = '';
  dossier.sections.forEach((section, index) => {
    const card = sectionTemplate.content.firstElementChild.cloneNode(true);
    card.style.setProperty('--delay', `${index * 70}ms`);
    card.querySelector('.section-eyebrow').textContent = section.label;
    card.querySelector('h3').textContent = section.title;
    card.querySelector('.section-body').textContent = section.body;
    sectionGrid.appendChild(card);
  });

  if (!dossier.sections.length) {
    const empty = document.createElement('article');
    empty.className = 'section-card glass is-empty';
    empty.innerHTML = '<p class="card-label section-eyebrow">No sections</p><h3>Backend returned no section data</h3><p class="section-body">Try Preview only first, then persist the run once the response looks correct.</p>';
    sectionGrid.appendChild(empty);
  }
}

async function requestDossier(endpoint, messages) {
  const payload = buildPayload();
  const words = tokenize(payload.brief).length;
  if (words < 8) {
    setStatus('Add a little more context before generating: user, input material, and expected output.', 'warning');
    setAlert(
      'Brief is too thin.',
      'Add the user, source material, expected output, and one review constraint before generating a saved blueprint.',
      'warning',
    );
    projectBrief.focus();
    return;
  }

  writeStoredValue('caseforge:lastBrief', payload.brief);
  writeFormState();
  setBusy(true);
  setStatus(messages.pending, 'pending');
  setAlert('Working on the blueprint.', messages.pending, 'pending');
  transportChip.textContent = 'Backend: connecting';

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    renderDossier(data, { source: messages.source });
    setStatus(messages.success, 'success');
    setAlert(messages.success, endpoint === '/api/dossiers' ? 'Export paths are now available in the saved-run bundle.' : 'No files were written during preview.', 'success');
    if (endpoint === '/api/dossiers') {
      refreshRecentDossiers();
    }
  } catch (error) {
    transportChip.textContent = 'Backend: unavailable';
    sourceChip.textContent = 'Source: last successful render';
    markdownChip.textContent = 'Markdown: unavailable';
    markdownPath.textContent = 'No export path available while the backend is unavailable.';
    exportMarkdownPath.textContent = 'Not saved yet';
    exportJsonPath.textContent = 'Not saved yet';
    exportSummaryPath.textContent = 'Not saved yet';
    setStatus(`${messages.failure} ${error.message}`, 'warning');
    setAlert(
      messages.failure,
      `Recovery: confirm the local server is running, keep provider set to deterministic, then retry Preview only. ${error.message}`,
      'warning',
    );
  } finally {
    setBusy(false);
    renderCompareSelectionState();
  }
}

function setBusy(isBusy) {
  document.body.classList.toggle('is-busy', isBusy);
  const labels = [
    [forgeButton, 'Forging...', 'Forge blueprint'],
    [previewButton, 'Previewing...', 'Preview only'],
  ];
  labels.forEach(([button, busyLabel, idleLabel]) => {
    if (button) {
      button.textContent = isBusy ? busyLabel : idleLabel;
    }
  });
  [forgeButton, previewButton, sampleButton, copyBriefButton, copyMarkdownButton, refreshRecentButton, compareButton, clearCompareButton].forEach(
    (button) => {
      if (button) {
        button.disabled = isBusy;
      }
    },
  );
}

function buildLocalDossier(payload) {
  const brief = payload.brief.toLowerCase();
  const theme = detectTheme(brief);
  return {
    title: theme.title,
    summary:
      `This project turns ${theme.user} pain into a focused ${payload.mode.toLowerCase()} that helps a ${payload.audience.toLowerCase()} see clear outcomes and a believable shipping plan.`,
    insights: [
      `Audience: ${payload.audience}`,
      `Mode: ${payload.mode}`,
      `Goal: ${payload.goal}`,
      `Preset: ${payload.preset}`,
      `Provider: ${payload.provider}`,
    ],
    sections: [
      {
        label: 'Problem',
        title: 'The user pain',
        body: theme.problem,
      },
      {
        label: 'Approach',
        title: 'The product angle',
        body: theme.approach,
      },
      {
        label: 'Architecture',
        title: 'The build plan',
        body: 'A local web app calls a deterministic blueprint pipeline and renders a concise artifact for implementation review.',
      },
      {
        label: 'Tradeoffs',
        title: 'What to manage',
        body: 'Keep the first release narrow and make blueprint quality the thesis of the product.',
      },
      {
        label: 'Delivery story',
        title: 'How to move it forward',
        body: 'Lead with the problem, then the pipeline, then the scope cuts that make the implementation path credible.',
      },
    ],
    persisted: false,
    preview: true,
    markdownPath: '',
    jsonPath: '',
    summaryPath: '',
    provider: payload.provider,
    providerStatus: 'local sample',
    providerMessage: 'Local browser sample, not a persisted backend run.',
    score: null,
    recommendation: 'Preview the backend to score this brief',
  };
}

function detectTheme(text) {
  if (text.includes('ops') || text.includes('incident') || text.includes('release') || text.includes('service')) {
    return {
      title: 'OpsFrame',
      user: 'operator',
      problem: 'Operational work is fast, fragmented, and difficult to convert into clear follow-up ownership.',
      approach: 'A guided workflow converts raw operational context into a practical action plan, risk summary, and delivery cadence.',
    };
  }
  if (text.includes('study') || text.includes('lecture') || text.includes('exam')) {
    return {
      title: 'Study Arc',
      user: 'student',
      problem: 'Students collect notes and links, but the material rarely turns into a revision system.',
      approach: 'An AI study companion turns passive content into quizzes, summaries, and a revision cadence that is easy to follow.',
    };
  }
  return {
    title: 'ForgeLine',
    user: 'builder',
    problem: 'Good ideas usually arrive before the structure that makes them believable.',
    approach: 'A focused AI product converts ambiguity into an artifact that can be reviewed, iterated, and discussed.',
  };
}

async function refreshRecentDossiers() {
  try {
    const response = await fetch('/api/dossiers?limit=8', {
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    recentDossiers = data.items || [];
    pruneCompareSelection();
    renderRecentDossiers(recentDossiers);
    renderCompareSelectionState();
  } catch {
    recentDossiers = [];
    compareSelection.clear();
    renderRecentDossiers([]);
    renderCompareSelectionState();
  }
}

function renderRecentDossiers(items) {
  recentList.innerHTML = '';
  if (!items.length) {
    const empty = document.createElement('p');
    empty.className = 'recent-empty';
    empty.textContent = 'No saved blueprints yet. Use Forge blueprint to create a persisted run, or Preview only to test the pipeline without writing files.';
    recentList.appendChild(empty);
    return;
  }

  items.forEach((item) => {
    const selected = compareSelection.has(item.slug);
    const card = document.createElement('article');
    card.className = `recent-item${selected ? ' is-selected' : ''}`;

    const header = document.createElement('div');
    header.className = 'recent-item-header';

    const title = document.createElement('strong');
    title.textContent = item.title;

    const timestamp = document.createElement('span');
    timestamp.className = 'recent-timestamp';
    timestamp.textContent = formatTimestamp(item.created_at);
    header.append(title, timestamp);

    const meta = document.createElement('div');
    meta.className = 'recent-item-meta';
    meta.append(
      buildRecentChip(item.score || 'unknown', 'score'),
      buildRecentChip(item.recommendation || 'unknown', 'recommendation'),
      buildRecentChip(item.preset || 'general', 'preset'),
      buildRecentChip(formatProviderLabel(item), 'provider'),
    );

    const slug = document.createElement('span');
    slug.className = 'recent-timestamp';
    slug.textContent = item.slug;

    const summary = document.createElement('p');
    summary.className = 'recent-item-summary';
    summary.textContent = item.summary || `Goal: ${item.goal || 'unknown'}.`;

    const footer = document.createElement('div');
    footer.className = 'recent-item-footer';
    footer.append(slug);

    const actions = document.createElement('div');
    actions.className = 'recent-actions';

    const openButton = document.createElement('button');
    openButton.type = 'button';
    openButton.className = 'recent-action';
    openButton.textContent = 'Open blueprint';
    openButton.addEventListener('click', () => loadSavedDossier(item.slug));

    const compareToggle = document.createElement('button');
    compareToggle.type = 'button';
    compareToggle.className = `recent-action${selected ? ' selected' : ''}`;
    compareToggle.textContent = selected ? 'Selected for compare' : 'Select for compare';
    compareToggle.disabled = !selected && compareSelection.size >= 2;
    compareToggle.addEventListener('click', () => toggleCompareSelection(item.slug));

    actions.append(openButton, compareToggle);
    footer.append(actions);
    card.append(header, meta, summary, footer);
    recentList.appendChild(card);
  });
}

function buildRecentChip(value, label) {
  const chip = document.createElement('span');
  chip.className = 'recent-chip';
  chip.textContent = `${label}: ${value}`;
  return chip;
}

function formatProviderLabel(item) {
  const providerName = item.provider || 'deterministic';
  const providerStatus = item.provider_status || 'deterministic';
  return `${providerName} (${providerStatus})`;
}

function formatTimestamp(value) {
  if (!value) {
    return 'unknown time';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function pruneCompareSelection() {
  const validSlugs = new Set(recentDossiers.map((item) => item.slug));
  [...compareSelection].forEach((slug) => {
    if (!validSlugs.has(slug)) {
      compareSelection.delete(slug);
    }
  });
}

function toggleCompareSelection(slug) {
  if (compareSelection.has(slug)) {
    compareSelection.delete(slug);
  } else if (compareSelection.size < 2) {
    compareSelection.add(slug);
  } else {
    setStatus('Select at most two saved blueprints for comparison.', 'warning');
    return;
  }

  renderRecentDossiers(recentDossiers);
  renderCompareSelectionState();
}

function renderCompareSelectionState() {
  const selected = [...compareSelection];
  compareButton.disabled = selected.length !== 2;

  if (!selected.length) {
    compareSelectionLabel.textContent = 'Select up to two saved runs to compare.';
    return;
  }

  compareSelectionLabel.textContent =
    selected.length === 1
      ? `Selected: ${selected[0]}. Choose one more run to compare.`
      : `Ready to compare: ${selected[0]} vs ${selected[1]}.`;
}

async function runComparison() {
  const selected = [...compareSelection];
  if (selected.length !== 2) {
    setStatus('Pick exactly two saved blueprints before comparing them.', 'warning');
    return;
  }

  setStatus('Loading blueprint comparison...', 'pending');
  try {
    const params = new URLSearchParams();
    selected.forEach((slug) => params.append('slug', slug));
    const response = await fetch(`/api/dossiers/compare?${params.toString()}`, {
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    renderComparison(data);
    setStatus('Comparison loaded from saved blueprints.', 'success');
  } catch (error) {
    renderComparison(null);
    setStatus(`Could not compare saved blueprints. ${error.message}`, 'warning');
  }
}

function renderComparison(payload) {
  compareResult.innerHTML = '';
  if (!payload || !Array.isArray(payload.items) || payload.items.length !== 2) {
    const empty = document.createElement('p');
    empty.className = 'recent-empty';
    empty.textContent = 'No comparison loaded yet.';
    compareResult.appendChild(empty);
    return;
  }

  const summary = document.createElement('p');
  summary.className = 'compare-summary';
  summary.textContent = payload.summary || 'Comparison loaded.';
  const decision = document.createElement('div');
  decision.className = 'compare-decision';
  const decisionLabel = document.createElement('span');
  decisionLabel.textContent = 'Decision note';
  const decisionCopy = document.createElement('p');
  decisionCopy.textContent = payload.decision_note || 'Use the comparison to decide which run is strong enough to become the implementation handoff.';
  decision.append(decisionLabel, decisionCopy);
  compareResult.append(decision, summary);

  const grid = document.createElement('div');
  grid.className = 'compare-grid';

  payload.items.forEach((item) => {
    const card = document.createElement('article');
    card.className = `compare-card${payload.winner_slug === item.slug ? ' is-winner' : ''}`;

    const title = document.createElement('h4');
    title.textContent = item.title;

    const slug = document.createElement('p');
    slug.className = 'recent-timestamp';
    slug.textContent = item.slug;

    const summaryText = document.createElement('p');
    summaryText.textContent = item.summary;

    const facts = document.createElement('dl');
    facts.className = 'compare-kv';
    facts.append(
      buildCompareRow('Score', item.score),
      buildCompareRow('Recommendation', item.recommendation),
      buildCompareRow('Preset', item.preset),
      buildCompareRow('Provider', `${item.provider} (${item.provider_status})`),
      buildCompareRow('Goal', item.goal),
      buildCompareRow('Top strength', item.top_strength),
      buildCompareRow('Top risk', item.top_risk),
    );

    card.append(title, slug, summaryText, facts);
    grid.appendChild(card);
  });

  compareResult.appendChild(grid);
}

function buildCompareRow(label, value) {
  const row = document.createElement('div');
  const term = document.createElement('dt');
  term.textContent = label;
  const detail = document.createElement('dd');
  detail.textContent = value || 'unknown';
  row.append(term, detail);
  return row;
}

async function loadSavedDossier(slug) {
  try {
    const response = await fetch(`/api/dossiers/${slug}`, {
      headers: {
        Accept: 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const data = await response.json();
    renderDossier(data, { source: 'saved blueprint' });
    setStatus(`Loaded saved blueprint ${slug}.`, 'success');
  } catch (error) {
    setStatus(`Could not load saved blueprint. ${error.message}`, 'warning');
  }
}

async function copyText(text, successMessage) {
  if (!text) {
    setStatus('Nothing to copy yet.', 'warning');
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus(successMessage, 'success');
  } catch {
    setStatus('Clipboard access failed in this browser.', 'warning');
  }
}

function setStatus(message, kind) {
  statusLine.textContent = message;
  statusLine.dataset.kind = kind;
}

function setAlert(title, message, kind) {
  if (!alertPanel) {
    return;
  }
  alertPanel.dataset.kind = kind;
  alertPanel.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span>`;
}

function capitalize(value) {
  const text = String(value || '').trim();
  return text ? `${text[0].toUpperCase()}${text.slice(1)}` : 'Unknown';
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

briefForm.addEventListener('submit', (event) => {
  event.preventDefault();
  requestDossier('/api/dossiers', {
    pending: 'Sending brief to /api/dossiers...',
    success: 'Blueprint generated from backend response.',
    failure: 'Backend unavailable, blueprint generation failed.',
    source: 'backend',
  });
});

previewButton.addEventListener('click', () => {
  requestDossier('/api/dossiers/preview', {
    pending: 'Sending brief to /api/dossiers/preview...',
    success: 'Preview generated without saving a blueprint.',
    failure: 'Preview endpoint unavailable.',
    source: 'backend preview',
  });
});

projectBrief.addEventListener('input', () => {
  updateMeta();
  writeStoredValue('caseforge:lastBrief', projectBrief.value);
  writeFormState();
});

[audience, mode, goal, preset, provider].forEach((field) => {
  field.addEventListener('change', writeFormState);
});

document.querySelectorAll('.preset').forEach((button) => {
  button.addEventListener('click', () => loadPreset(button.dataset.preset));
});

sampleButton.addEventListener('click', () => {
  renderDossier(buildLocalDossier(buildPayload()), { source: 'local sample' });
  setStatus('Sample blueprint loaded.', 'success');
});

copyBriefButton.addEventListener('click', () => {
  copyText(projectBrief.value.trim(), 'Brief copied to clipboard.');
});

copyMarkdownButton.addEventListener('click', () => {
  copyText(markdownPath.textContent.trim(), 'Markdown path copied.');
});

refreshRecentButton.addEventListener('click', () => {
  refreshRecentDossiers();
  setStatus('Recent blueprints refreshed.', 'success');
});

compareButton.addEventListener('click', () => {
  runComparison();
});

clearCompareButton.addEventListener('click', () => {
  compareSelection.clear();
  renderRecentDossiers(recentDossiers);
  renderCompareSelectionState();
  renderComparison(null);
  setStatus('Comparison selection cleared.', 'success');
});

window.addEventListener('DOMContentLoaded', bootstrap);
