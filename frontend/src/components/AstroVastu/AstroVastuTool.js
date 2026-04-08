import React, { useMemo, useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import { useAstrology } from '../../context/AstrologyContext';
import './AstroVastuTool.css';

const DOOR_OPTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];

const TAG_DEFS = [
  { id: 'toilet_bath', label: 'Toilet / bath' },
  { id: 'master_bedroom', label: 'Master bedroom' },
  { id: 'kids_room', label: 'Kids room' },
  { id: 'kitchen_fire', label: 'Kitchen / stove' },
  { id: 'desk', label: 'Desk / study' },
  { id: 'study_room', label: 'Study room' },
  { id: 'living_room', label: 'Living room' },
  { id: 'temple_prayer', label: 'Temple / prayer' },
  { id: 'garden_plants', label: 'Garden / plants' },
  { id: 'water_body', label: 'Water body / tank' },
  { id: 'balcony_open', label: 'Balcony / open space' },
  { id: 'store_clutter', label: 'Storage / clutter' },
  { id: 'main_door', label: 'Main door' },
  { id: 'empty', label: 'Mostly empty' },
  { id: 'other', label: 'Other' },
];

function emptyZoneState() {
  const z = {};
  DOOR_OPTIONS.forEach((d) => {
    z[d] = [];
  });
  return z;
}

function normalizedTagsObject(zoneTags) {
  const out = {};
  DOOR_OPTIONS.forEach((d) => {
    const tags = zoneTags[d];
    if (tags && tags.length) out[d] = [...tags].map(String).sort();
  });
  return out;
}

function normalizeSavedTags(raw) {
  if (!raw || typeof raw !== 'object') return {};
  const out = {};
  Object.keys(raw).forEach((d) => {
    const t = raw[d];
    if (Array.isArray(t) && t.length) out[d] = [...t].map(String).sort();
  });
  return out;
}

function birthMatchesSavedBirth(req, birthPayload) {
  if (!req?.birth_data || !birthPayload?.date) return false;
  const b = req.birth_data;
  const sb = String(b?.date || '').split('T')[0];
  const cb = String(birthPayload.date || '').split('T')[0];
  return (
    sb === cb &&
    String(b?.time || '') === String(birthPayload.time || '') &&
    Number(b?.latitude) === Number(birthPayload.latitude) &&
    Number(b?.longitude) === Number(birthPayload.longitude)
  );
}

function goalsCompatibleWithSaved(reqGoal, currentGoal) {
  const c = String(currentGoal || '').toLowerCase();
  if (c === 'complete_all') return true;
  return String(reqGoal || '').toLowerCase() === c;
}

function currentInputsMatchSaved(req, birthPayload, goal, door, zoneTags) {
  if (!req || !birthPayload?.date) return false;
  const sameBirth = birthMatchesSavedBirth(req, birthPayload);
  const sameGoal = goalsCompatibleWithSaved(req.goal, goal);
  const sameDoor = String(req.door_facing || '') === String(door || '');
  const sTags = JSON.stringify(normalizeSavedTags(req.zone_tags));
  const cTags = JSON.stringify(normalizedTagsObject(zoneTags));
  return sameBirth && sameGoal && sameDoor && sTags === cTags;
}

function applyRequestToForm(req, setGoal, setDoor, setZoneTags) {
  if (!req) return;
  // Complete-analysis mode only: ignore any legacy saved goal like "career"
  setGoal('complete_all');
  setDoor(req.door_facing || 'E');
  if (req.zone_tags && typeof req.zone_tags === 'object') {
    const z = emptyZoneState();
    Object.keys(req.zone_tags).forEach((d) => {
      if (z[d] !== undefined) z[d] = [...req.zone_tags[d]];
    });
    setZoneTags(z);
  } else {
    setZoneTags(emptyZoneState());
  }
}

function renderParagraphs(text) {
  if (!text) return null;
  return text
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p, i) => (
      <p key={i} className="astrovastu-ai-paragraph">
        {p}
      </p>
    ));
}

function SmartList({ items, empty = null }) {
  if (!items || !items.length) return empty;
  return (
    <ul className="astrovastu-remedy-list">
      {items.map((x, i) => (
        <li key={i}>{x}</li>
      ))}
    </ul>
  );
}

function HomeDirectionSvg({ result }) {
  const dirs = result?.directions || {};
  const sectorThemeLine = (row) => {
    const ht = row.house_life_themes || {};
    const occ = ht.houses_with_planets_themes;
    const mapped = ht.mapped_houses_with_themes;
    const pick = Array.isArray(occ) && occ.length ? occ : mapped;
    if (!Array.isArray(pick) || !pick.length) return 'Whole-sign houses in this wind';
    return pick.slice(0, 2).join(' · ');
  };
  const cells = [
    ['NW', 0, 0], ['N', 1, 0], ['NE', 2, 0],
    ['W', 0, 1], ['C', 1, 1], ['E', 2, 1],
    ['SW', 0, 2], ['S', 1, 2], ['SE', 2, 2],
  ];
  const box = 194;
  const gap = 8;
  const size = box * 3 + gap * 2;
  const xFor = (c) => c * (box + gap);
  const yFor = (r) => r * (box + gap);
  const chipsBlock = (items, type) => {
    const list = Array.isArray(items) && items.length ? items : ['none'];
    return (
      <div className={`astrovastu-svg-chip-wrap astrovastu-svg-chip-wrap--${type}`}>
        {list.map((item, i) => (
          <span key={`${type}-${i}-${item}`} className={`astrovastu-svg-chip astrovastu-svg-chip--${type}`}>
            {item}
          </span>
        ))}
      </div>
    );
  };
  return (
    <svg className="astrovastu-home-svg" viewBox={`0 0 ${size} ${size}`} role="img" aria-label="AstroVastu home direction map">
      <defs>
        <linearGradient id="avBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fffafc" />
          <stop offset="100%" stopColor="#fce4ec" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width={size} height={size} rx="18" fill="url(#avBg)" />
      {cells.map(([dir, c, r]) => {
        const x = xFor(c);
        const y = yFor(r);
        if (dir === 'C') {
          return (
            <g key="center">
              <rect x={x} y={y} width={box} height={box} rx="12" fill="#fff" stroke="#f8bbd0" />
              <text x={x + box / 2} y={y + 64} textAnchor="middle" fontSize="18" fill="#ad1457" fontWeight="700">Home</text>
              <text x={x + box / 2} y={y + 94} textAnchor="middle" fontSize="12" fill="#7b1fa2">Planet map</text>
            </g>
          );
        }
        const row = dirs[dir] || {};
        const mappedSigns = row.mapped_signs || row.signs || [];
        const planets = row.planets || [];
        const housesSource = (row.house_numbers && row.house_numbers.length > 0)
          ? row.house_numbers
          : (row.mapped_house_numbers || []);
        const houses = housesSource.map((h) => `H${h}`);
        const lifeArea = sectorThemeLine(row);
        return (
          <g key={dir}>
            <rect x={x} y={y} width={box} height={box} rx="12" fill="#fff" stroke="#f8bbd0" />
            <text x={x + 10} y={y + 22} fontSize="14" fill="#880e4f" fontWeight="700">{dir}</text>
            <text x={x + 10} y={y + 36} fontSize="10" fill="#6d4c41">{lifeArea}</text>
            <text x={x + 10} y={y + 52} fontSize="10" fill="#4e342e" fontWeight="600">Signs</text>
            <foreignObject x={x + 8} y={y + 56} width={box - 16} height={44}>
              {chipsBlock(mappedSigns, 'sign')}
            </foreignObject>
            <text x={x + 10} y={y + 108} fontSize="10" fill="#4e342e" fontWeight="600">Houses</text>
            <foreignObject x={x + 8} y={y + 112} width={box - 16} height={32}>
              {chipsBlock(houses, 'house')}
            </foreignObject>
            <text x={x + 10} y={y + 154} fontSize="10" fill="#4e342e" fontWeight="600">Planets</text>
            <foreignObject x={x + 8} y={y + 158} width={box - 16} height={32}>
              {chipsBlock(planets, 'planet')}
            </foreignObject>
          </g>
        );
      })}
    </svg>
  );
}

export default function AstroVastuTool({ user, onLogout, onAdminClick, onLogin }) {
  const navigate = useNavigate();
  const { birthData, setBirthData } = useAstrology();
  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState('complete_all');
  const [door, setDoor] = useState('E');
  const [zoneTags, setZoneTags] = useState(() => emptyZoneState());
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [savedSnapshot, setSavedSnapshot] = useState(null);
  /** User chose "Start from beginning" on this mount — do not immediately reload server map over their choice. */
  const skipAutoRestoreRef = useRef(false);

  const birthPayload = useMemo(() => {
    if (!birthData) return null;
    return {
      name: birthData.name || 'User',
      date: birthData.date,
      time: birthData.time,
      latitude: birthData.latitude,
      longitude: birthData.longitude,
      timezone: birthData.timezone || '',
      place: birthData.place || '',
      gender: birthData.gender || '',
    };
  }, [birthData]);

  /** Birth sent to /analyze: use context, or fall back to last saved request if time/date missing in context. */
  const analyzeBirthPayload = useMemo(() => {
    if (birthPayload?.date && birthPayload?.time) return birthPayload;
    const b = savedSnapshot?.request?.birth_data;
    if (b?.date && b?.time) {
      return {
        name: birthPayload?.name || b.name || 'User',
        date: b.date,
        time: b.time,
        latitude: birthPayload?.latitude ?? b.latitude,
        longitude: birthPayload?.longitude ?? b.longitude,
        timezone: birthPayload?.timezone || b.timezone || '',
        place: birthPayload?.place || b.place || '',
        gender: birthPayload?.gender || b.gender || '',
      };
    }
    return birthPayload;
  }, [birthPayload, savedSnapshot]);

  const refreshSavedFromServer = useCallback(async () => {
    if (!user) return;
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const { data } = await axios.get('/api/astrovastu/latest', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (data.has_saved) setSavedSnapshot(data);
      else setSavedSnapshot(null);
    } catch {
      /* offline / 401 — ignore */
    }
  }, [user]);

  useEffect(() => {
    refreshSavedFromServer();
  }, [refreshSavedFromServer]);

  useEffect(() => {
    if (!user || skipAutoRestoreRef.current) return;
    if (!savedSnapshot?.has_saved || !savedSnapshot.request || !savedSnapshot.result) return;
    if (!birthPayload?.date) return;
    if (!birthMatchesSavedBirth(savedSnapshot.request, birthPayload)) return;
    const req = savedSnapshot.request;
    applyRequestToForm(req, setGoal, setDoor, setZoneTags);
    const b = req.birth_data;
    if (b && setBirthData) {
      setBirthData((prev) => ({
        ...(prev || {}),
        name: b.name,
        date: b.date,
        time: b.time,
        latitude: b.latitude,
        longitude: b.longitude,
        timezone: b.timezone ?? '',
        place: b.place ?? '',
        gender: b.gender ?? '',
      }));
    }
    setResult(savedSnapshot.result);
    setStep(6);
    setError(null);
  }, [user, savedSnapshot, birthPayload, setBirthData]);

  const loadSavedMap = useCallback(() => {
    if (!savedSnapshot?.result || !savedSnapshot.request) return;
    const req = savedSnapshot.request;
    applyRequestToForm(req, setGoal, setDoor, setZoneTags);
    const b = req.birth_data;
    if (b && setBirthData) {
      setBirthData({
        ...birthData,
        name: b.name,
        date: b.date,
        time: b.time,
        latitude: b.latitude,
        longitude: b.longitude,
        timezone: b.timezone ?? '',
        place: b.place ?? '',
        gender: b.gender ?? '',
      });
    }
    setResult(savedSnapshot.result);
    setStep(6);
    setError(null);
    skipAutoRestoreRef.current = false;
  }, [savedSnapshot, birthData, setBirthData]);

  const inputsMatchSaved = useMemo(
    () =>
      Boolean(
        savedSnapshot?.request &&
          currentInputsMatchSaved(savedSnapshot.request, birthPayload, goal, door, zoneTags),
      ),
    [savedSnapshot, birthPayload, goal, door, zoneTags],
  );

  const toggleTag = (dir, tagId) => {
    setZoneTags((prev) => {
      const cur = [...(prev[dir] || [])];
      const i = cur.indexOf(tagId);
      if (i >= 0) cur.splice(i, 1);
      else cur.push(tagId);
      return { ...prev, [dir]: cur };
    });
  };

  const buildTagsForApi = () => {
    const out = {};
    DOOR_OPTIONS.forEach((d) => {
      const tags = zoneTags[d];
      if (tags && tags.length) out[d] = tags;
    });
    return Object.keys(out).length ? out : null;
  };

  const runAnalyze = async () => {
    if (!analyzeBirthPayload?.date || !analyzeBirthPayload?.time) {
      setError('Add your birth details first.');
      setShowBirthModal(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const { data } = await axios.post(
        '/api/astrovastu/analyze',
        {
          birth_data: analyzeBirthPayload,
          goal: 'complete_all',
          door_facing: door,
          zone_tags: buildTagsForApi(),
        },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
      );
      setResult(data);
      setStep(6);
      skipAutoRestoreRef.current = false;
      await refreshSavedFromServer();
    } catch (e) {
      const d = e.response?.data?.detail;
      setError(typeof d === 'string' ? d : e.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="astrovastu-page">
      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={!user}
        onCreditsClick={() => navigate('/credits')}
        birthData={birthData}
        onChangeNative={() => setShowBirthModal(true)}
        onHomeClick={() => navigate('/')}
      />
      <div className="astrovastu-shell">
        <h1>AstroVastu</h1>
        <p className="astrovastu-lead">
          Chart-first mapping: each planet’s <strong>sign</strong> fixes its compass sector (door does not spin the chart).{' '}
          <strong>Mapping {result?.mapping_version || 'v2'}</strong>
        </p>

        {error && <div className="astrovastu-error">{error}</div>}

        {user && savedSnapshot?.has_saved && (
          <div className="astrovastu-saved-card">
            <h2 className="astrovastu-saved-title">Saved map</h2>
            <p className="astrovastu-saved-meta">
              Stored on your account — last updated{' '}
              <strong>{new Date(savedSnapshot.updated_at).toLocaleString()}</strong>
              {savedSnapshot.mapping_version ? (
                <>
                  {' '}
                  · mapping <code>{savedSnapshot.mapping_version}</code>
                </>
              ) : null}
            </p>
            {inputsMatchSaved ? (
              <p className="astrovastu-saved-match">
                This matches your current birth profile, goal, door, and tags — you can reopen it instantly without running the calculator again.
              </p>
            ) : (
              <p className="astrovastu-saved-diff">
                Your current choices differ from this save. Opening will load the saved birth, goal, door, and room tags so the map matches what
                was stored.
              </p>
            )}
            <div className="astrovastu-saved-actions">
              <button type="button" className="astrovastu-primary" onClick={loadSavedMap}>
                Open saved map
              </button>
              <button type="button" className="astrovastu-secondary" onClick={() => setSavedSnapshot(null)}>
                Hide for now
              </button>
            </div>
          </div>
        )}

        {step === 0 && (
          <div className="astrovastu-card">
            <h2>Complete AstroVastu analysis</h2>
            <p style={{ color: '#555', lineHeight: 1.5 }}>
              We generate one complete AI report across career, wealth, relationship/family, health, focus, and spiritual-home harmony. The model
              uses your chart-to-direction map, room tags, and active dashas as timing context.
            </p>
            <button type="button" className="astrovastu-primary" onClick={() => setStep(2)}>
              Start — about 2 minutes
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="astrovastu-card">
            <h2>Your birth details</h2>
            {birthPayload?.date ? (
              <>
                <p style={{ color: '#444' }}>
                  Using <strong>{birthPayload.name}</strong> — {String(birthPayload.date).split('T')[0]} at {birthPayload.time},{' '}
                  {birthPayload.place || `${birthPayload.latitude}, ${birthPayload.longitude}`}
                </p>
                <button type="button" className="astrovastu-secondary" onClick={() => setShowBirthModal(true)}>
                  Edit details
                </button>
              </>
            ) : (
              <p style={{ color: '#666' }}>No saved birth profile yet.</p>
            )}
            <button
              type="button"
              className="astrovastu-primary"
              onClick={() => {
                if (!birthPayload?.date) setShowBirthModal(true);
                else setStep(3);
              }}
            >
              {birthPayload?.date ? 'Use this chart' : 'Add birth details'}
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="astrovastu-card">
            <h2>Main door faces which direction?</h2>
            <p style={{ fontSize: '0.9rem', color: '#666' }}>
              Approximate is fine (±15°). Standing inside, looking out through the main entrance. This labels your entrance sector for tags — it
              does not rotate sign-based directions.
            </p>
            <div className="astrovastu-door-grid">
              {DOOR_OPTIONS.map((d) => (
                <button
                  key={d}
                  type="button"
                  className={`astrovastu-door-btn ${door === d ? 'active' : ''}`}
                  onClick={() => setDoor(d)}
                >
                  {d}
                </button>
              ))}
            </div>
            <button type="button" className="astrovastu-primary" onClick={() => setStep(4)}>
              Continue
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="astrovastu-card">
            <h2>Tag your home (optional)</h2>
            <p style={{ fontSize: '0.9rem', color: '#666' }}>
              For each direction, select what dominates that sector. Skip any you are unsure about.
            </p>
            {DOOR_OPTIONS.map((d) => (
              <div key={d} className="astrovastu-zone-row">
                <strong>{d}</strong>
                <div className="astrovastu-tag-chips">
                  {TAG_DEFS.map((t) => (
                    <label key={t.id}>
                      <input
                        type="checkbox"
                        checked={(zoneTags[d] || []).includes(t.id)}
                        onChange={() => toggleTag(d, t.id)}
                      />
                      {t.label}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            <button
              type="button"
              className="astrovastu-primary"
              disabled={loading}
              onClick={() => {
                setStep(5);
                setTimeout(() => runAnalyze(), 0);
              }}
            >
              {loading ? 'Mapping…' : 'Build my energy map'}
            </button>
            <button
              type="button"
              className="astrovastu-secondary"
              disabled={loading}
              onClick={() => {
                setZoneTags(emptyZoneState());
                setStep(5);
                setTimeout(() => runAnalyze(), 0);
              }}
            >
              Skip tags &amp; use chart only
            </button>
          </div>
        )}

        {step === 5 && loading && (
          <div className="astrovastu-card">
            <h2>Mapping signs to compass sectors…</h2>
            <p style={{ color: '#666' }}>Building explanations from your chart, goal, and room tags.</p>
          </div>
        )}

        {step === 6 && result && (
          <>
            {loading && (
              <div className="astrovastu-regenerating-bar" role="status" aria-live="polite">
                Regenerating analysis…
              </div>
            )}
            {result.ai ? (
              <div className={`astrovastu-card${loading ? ' astrovastu-card--dim' : ''}`}>
                <h2>Complete AstroVastu analysis</h2>
                <HomeDirectionSvg result={result} />
                {!!result.ai.snapshot?.topline && (
                  <div className="astrovastu-section-card">
                    <h3>Snapshot</h3>
                    <p className="astrovastu-ai-exec">{result.ai.snapshot.topline}</p>
                    {!!result.ai.snapshot?.current_dasha_note && (
                      <p className="astrovastu-methodology-text">{result.ai.snapshot.current_dasha_note}</p>
                    )}
                    <SmartList items={result.ai.snapshot?.top_directions || []} />
                  </div>
                )}
                {result.ai.executive_summary_ai && (
                  <p className="astrovastu-ai-exec">{result.ai.executive_summary_ai}</p>
                )}
                {!!result.ai.what_this_means && Object.keys(result.ai.what_this_means).length > 0 && (
                  <div className="astrovastu-section-card">
                    <h3>What This Means For You</h3>
                    {Object.entries(result.ai.what_this_means).map(([k, v]) => (
                      <div key={k} className="astrovastu-area-block">
                        <strong>{k.replace(/_/g, ' ')}</strong>
                        <p className="astrovastu-methodology-text">{String(v)}</p>
                      </div>
                    ))}
                  </div>
                )}
                {!!result.ai.direction_ai && Object.keys(result.ai.direction_ai).length > 0 && (
                  <div className="astrovastu-section-card">
                    <h3>Direction-by-Direction</h3>
                    {Object.entries(result.ai.direction_ai).map(([d, txt]) => (
                      <div key={d} className="astrovastu-area-block">
                        <strong>{d}</strong>
                        <p className="astrovastu-methodology-text">{String(txt)}</p>
                      </div>
                    ))}
                  </div>
                )}
                {(result.ai.room_specific_guidance || []).length > 0 && (
                  <div className="astrovastu-section-card">
                    <h3>Room-Specific Guidance</h3>
                    {(result.ai.room_specific_guidance || []).map((row, i) => (
                      <div key={i} className="astrovastu-area-block">
                        <strong>{row.room_tag} in {row.direction} ({row.status})</strong>
                        <p className="astrovastu-methodology-text">{row.advice}</p>
                      </div>
                    ))}
                  </div>
                )}
                {!!result.ai.timing_plan && (
                  <div className="astrovastu-section-card">
                    <h3>Timing Plan</h3>
                    <strong>Now (0-3 months)</strong>
                    <SmartList items={result.ai.timing_plan?.now_0_3_months || []} />
                    <strong>3-6 months</strong>
                    <SmartList items={result.ai.timing_plan?.months_3_6 || []} />
                    <strong>6-18 months</strong>
                    <SmartList items={result.ai.timing_plan?.months_6_18 || []} />
                  </div>
                )}
                {!!result.ai.action_plan && (
                  <div className="astrovastu-section-card">
                    <h3>Action Plan</h3>
                    <strong>This week</strong>
                    <SmartList items={result.ai.action_plan?.this_week || []} />
                    <strong>This month</strong>
                    <SmartList items={result.ai.action_plan?.this_month || []} />
                    <strong>Optional upgrades</strong>
                    <SmartList items={result.ai.action_plan?.optional_upgrades || []} />
                  </div>
                )}
                {(result.ai.non_renovation_options || []).length > 0 && (
                  <div className="astrovastu-section-card">
                    <h3>If You Can’t Renovate</h3>
                    <SmartList items={result.ai.non_renovation_options || []} />
                  </div>
                )}
                {result.ai.full_analysis_ai && <div className="astrovastu-ai-full">{renderParagraphs(result.ai.full_analysis_ai)}</div>}
                {(result.ai.action_plan_ai || []).length > 0 && <SmartList items={result.ai.action_plan_ai} />}
                {result.ai.confidence_note_ai && (
                  <p className="astrovastu-meta">{result.ai.confidence_note_ai}</p>
                )}
              </div>
            ) : (
              <div className={`astrovastu-card${loading ? ' astrovastu-card--dim' : ''}`}>
                <h2>AI analysis unavailable</h2>
                <p className="astrovastu-methodology-text">
                  This result did not include an AI report. Please run the analysis again.
                </p>
              </div>
            )}

            <button
              type="button"
              className="astrovastu-secondary"
              disabled={loading}
              onClick={() => {
                // Keep existing door + room-direction mapping and reopen setup at mapping step
                setResult(null);
                setStep(4);
                setError(null);
              }}
            >
              Edit room-direction mapping
            </button>
            <button
              type="button"
              className="astrovastu-primary"
              disabled={loading}
              onClick={() => {
                // Stay on step 6 so the button is not unmounted mid-click (avoids ghost-open on header native chip)
                runAnalyze();
              }}
            >
              Regenerate analysis
            </button>
            <button
              type="button"
              className="astrovastu-secondary"
              disabled={loading}
              onClick={() => {
                // Hard reset only if user explicitly wants to start from intro
                skipAutoRestoreRef.current = true;
                setResult(null);
                setStep(0);
                setError(null);
              }}
            >
              Start from beginning
            </button>
          </>
        )}
      </div>

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={() => {
          if (step === 2) setStep(3);
        }}
        title="Birth details for AstroVastu"
        description="Accurate date, time, and place give correct sidereal signs for direction mapping."
      />
    </div>
  );
}
