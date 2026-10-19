import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Modal, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { exportHtmlAsPdf } from '../../utils/pdfGenerator';
import { buildMrityuBhagaReport, ordinal } from '../../utils/mrityuBhagaExport';
import { chartAPI } from '../../services/api';
import NorthIndianChart from './NorthIndianChart';
import { useTheme } from '../../context/ThemeContext';
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const plus = (value, days) => {
  const d = new Date(`${value}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};
const label = p => p === 'Ascendant' ? 'Lagna' : p === 'Mandi' ? 'Gulika / Mandi' : p;
const moment = (value, utc) => new Date(value).toLocaleString('en-GB', {
  ...(utc ? {
    timeZone: 'UTC'
  } : {}),
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit'
});
const links = rows => rows.map(r => `${{
  mahadasha: 'MD',
  antardasha: 'AD',
  pratyantardasha: 'PD'
}[r.level]}: ${r.lord} (${r.relation === 'direct' ? 'own period' : 'sign ruler'})`).join(' · ');
const strength = v => v ? `${v.total_rupas} rupas · ${v.required_percent}% of required strength` : 'Not applicable';
const foldCalendarLine = line => {
  let current = '',
    bytes = 0;
  const rows = [];
  for (const char of line) {
    const code = char.codePointAt(0),
      length = code > 65535 ? 4 : code > 2047 ? 3 : code > 127 ? 2 : 1;
    if (bytes + length > 73) {
      rows.push(current);
      current = ' ';
      bytes = 1;
    }
    current += char;
    bytes += length;
  }
  rows.push(current);
  return rows.join('\r\n');
};
const kind = r => r.kind === 'natal_mb_span' ? 'Passes through the Mrityu Bhaga range' : r.aspect_number === 1 ? 'Passes over the birth position' : `${ordinal(r.aspect_number)} aspect to the birth position`;
const icsDate = value => new Date(value).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z/, 'Z');
async function shareFile(name, text, mime) {
  if (Platform.OS === 'web') {
    const url = URL.createObjectURL(new Blob([text], {
      type: mime
    }));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return;
  }
  const uri = `${FileSystem.cacheDirectory}${name}`;
  await FileSystem.writeAsStringAsync(uri, text);
  await Sharing.shareAsync(uri, {
    mimeType: mime
  });
}
export default function MrityuBhagaPanel({
  birthData,
  visible,
  onClose,
  onAsk
}) {
  return <Modal visible={visible} animationType="slide" onRequestClose={onClose}>{visible && <Content key={JSON.stringify(birthData)} birthData={birthData} onClose={onClose} onAsk={onAsk} />}</Modal>;
}
function Button({
  children,
  onPress,
  active,
  disabled
}) {
  const {
    colors
  } = useTheme();
  return <TouchableOpacity accessibilityRole="button" accessibilityState={{
    disabled: !!disabled,
    selected: !!active
  }} disabled={disabled} onPress={onPress} style={[s.button, {
    backgroundColor: active ? '#dfcc99' : colors.surface,
    borderColor: '#b9a579',
    opacity: disabled ? .5 : 1
  }]}><Text style={{
      color: active ? '#29131e' : colors.text,
      fontWeight: '600'
    }}>{children}</Text></TouchableOpacity>;
}
function Body({
  children,
  style
}) {
  const {
    colors
  } = useTheme();
  return <Text style={[s.body, {
    color: colors.text
  }, style]}>{children}</Text>;
}
function Heading({
  children
}) {
  const {
    colors
  } = useTheme();
  return <Text style={[s.heading, {
    color: colors.text
  }]}>{children}</Text>;
}
function Card({
  children
}) {
  const {
    colors
  } = useTheme();
  return <View style={[s.card, {
    backgroundColor: colors.surface,
    borderColor: colors.cardBorder
  }]}>{children}</View>;
}
const Note = ({
  id,
  ready,
  value,
  onChange
}) => {
  const {
    colors
  } = useTheme();
  return <View style={{
    marginTop: 12
  }}><Body style={s.muted}>Astrologer notes / event review · this device</Body><TextInput accessibilityLabel={`Notes for ${id}`} editable={ready} multiline value={value} placeholder="Observation, including no notable event" placeholderTextColor={colors.textSecondary} onChangeText={onChange} style={[s.input, {
      backgroundColor: colors.surfaceMuted,
      color: colors.text,
      borderColor: colors.cardBorder,
      minHeight: 76,
      textAlignVertical: 'top'
    }]} /></View>;
};
function Content({
  birthData,
  onClose,
  onAsk
}) {
  const {
    colors
  } = useTheme();
  const [tab, setTab] = useState('natal'),
    [data, setData] = useState(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [start, setStart] = useState(today),
    [end, setEnd] = useState(() => plus(today(), 89)),
    [fast, setFast] = useState(false),
    [aspects, setAspects] = useState(false),
    [orb, setOrb] = useState(1);
  const [filter, setFilter] = useState('all'),
    [type, setType] = useState('all'),
    [multiple, setMultiple] = useState(false),
    [direct, setDirect] = useState(false),
    [utc, setUtc] = useState(false),
    [sensitivity, setSensitivity] = useState(0),
    [focusPoint, setFocusPoint] = useState(null),
    [all, setAll] = useState(false),
    [selected, setSelected] = useState(new Set());
  const [showChart, setShowChart] = useState(false),
    [notes, setNotes] = useState({}),
    [noteReady, setNoteReady] = useState(false);
  const [visibleCount, setVisibleCount] = useState(40);
  useEffect(() => setVisibleCount(40), [filter, type, direct, multiple, data]);
  const scroll = useRef(null);
  useEffect(() => {
    scroll.current?.scrollTo({
      y: 0,
      animated: false
    });
  }, [tab]);
  const controller = useRef(null),
    noteTimer = useRef(null),
    latestNotes = useRef({}),
    alive = useRef(true);
  const noteKey = `mb-notes-v1:${JSON.stringify([birthData.date, birthData.time, birthData.latitude, birthData.longitude, birthData.calculation_profile])}`;
  useEffect(() => {
    AsyncStorage.getItem(noteKey).then(v => {
      if (alive.current) {
        const saved = v ? JSON.parse(v) : {};
        setNotes(saved);
        latestNotes.current = saved;
        setNoteReady(true);
      }
    }).catch(() => {
      if (alive.current) {
        setError('Saved notes could not be loaded. Notes remain disabled to protect existing data.');
      }
    });
    return () => {
      alive.current = false;
      controller.current?.abort();
      clearTimeout(noteTimer.current);
    };
  }, []);
  const updateNote = (key, value) => {
    const next = {
      ...latestNotes.current,
      [key]: value
    };
    latestNotes.current = next;
    setNotes(next);
    clearTimeout(noteTimer.current);
    noteTimer.current = setTimeout(() => AsyncStorage.setItem(noteKey, JSON.stringify(next)).catch(() => {
      if (alive.current) setError('Notes could not be saved on this device.');
    }), 300);
  };
  useEffect(() => () => {
    if (noteReady) AsyncStorage.setItem(noteKey, JSON.stringify(latestNotes.current)).catch(() => {});
  }, [noteReady, noteKey]);
  async function load(calendar = false, comparison = sensitivity) {
    controller.current?.abort();
    const req = new AbortController();
    controller.current = req;
    setBusy(true);
    setError('');
    setSelected(new Set());
    try {
      const response = await chartAPI.getMrityuBhagaWorkspace(birthData, {
        start_date: start,
        end_date: end,
        calendar,
        include_fast: fast,
        include_aspects: aspects,
        orb_degrees: orb,
        birth_time_minutes: comparison
      }, req.signal);
      if (!req.signal.aborted) setData(response.data);
    } catch (e) {
      if (!req.signal.aborted) setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : e.message || 'Calculation unavailable.');
    } finally {
      if (!req.signal.aborted) setBusy(false);
    }
  }
  useEffect(() => {
    load(false);
  }, []);
  const invalidate = fn => {
    controller.current?.abort();
    setBusy(false);
    setData(p => p ? {
      ...p,
      calendar_calculated: false,
      events: [],
      dasha_activations: []
    } : p);
    fn();
  };
  const events = (data?.events || []).filter(r => (!multiple || r.concurrent_transits?.length) && (filter === 'all' || r.point === filter) && (type === 'all' || r.kind === type) && (!direct || r.dasha_overlaps.some(d => d.connections.some(c => c.relation === 'direct'))));
  const dashas = (data?.dasha_activations || []).filter(r => (filter === 'all' || r.point === filter) && (!direct || r.connections.some(c => c.relation === 'direct')));
  const exportCalendar = async () => {
    const text = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AstroRoshni//Mrityu Bhaga//EN', ...(data.events || []).filter(r => selected.has(r.id)).flatMap(r => ['BEGIN:VEVENT', `UID:${r.id}:${r.start_at}@astroroshni.com`, `DTSTAMP:${icsDate(new Date())}`, `DTSTART:${icsDate(r.start_at)}`, `DTEND:${icsDate(r.end_at)}`, `SUMMARY:${r.planet} - ${label(r.point)} - ${kind(r)}`, 'DESCRIPTION:Potential activation evidence. Review natal and dasha context in AstroRoshni.', 'END:VEVENT']), 'END:VCALENDAR'].map(foldCalendarLine).join('\r\n');
    try {
      await shareFile('AstroRoshni-MB.ics', text, 'text/calendar');
    } catch (e) {
      Alert.alert('Export unavailable', e.message);
    }
  };
  const exportPdf = async () => {
    if (exporting) return;
    setExporting(true);
    try {
      const html = buildMrityuBhagaReport(data, birthData, notes, events);
      const result = await exportHtmlAsPdf(html);
      if (Platform.OS !== 'web' && result) await Sharing.shareAsync(result, {
        mimeType: 'application/pdf'
      });
    } catch (e) {
      Alert.alert('PDF unavailable', e.message);
    } finally {
      if (alive.current) setExporting(false);
    }
  };
  return <SafeAreaView style={[s.root, {
    backgroundColor: colors.background
  }]}><View style={s.header}><View style={{
        flex: 1
      }}><Text style={{
          color: '#967631',
          fontSize: 11,
          letterSpacing: 1
        }}>ASTROROSHNI · CHARTS</Text><Heading>Mrityu Bhaga</Heading><Body>{birthData.name}</Body></View><Button onPress={onClose}>Close</Button></View><View style={s.row}>{['natal', 'calendar', 'audit'].map(t => <Button key={t} active={tab === t} onPress={() => setTab(t)}>{t === 'natal' ? 'Natal' : t === 'calendar' ? 'Calendar' : 'Audit'}</Button>)}</View>
    <ScrollView ref={scroll} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
      {!!error && <Card><Text accessibilityRole="alert" style={{
          color: '#a15a2a'
        }}>{error}</Text><Button onPress={() => load(tab === 'calendar')}>Retry</Button></Card>}{busy && <View accessibilityLiveRegion="polite" style={s.row}><ActivityIndicator color="#967631" /><Body>Calculating {tab === 'calendar' ? 'exact windows and dasha overlaps' : 'natal evidence'}…</Body></View>}
      {data?.natal.unavailable_points?.map(p => <Card key={p.point}><Body>Assessment incomplete: {p.point} could not be checked. {p.reason} Its absence is not a negative finding.</Body></Card>)}
      {data && tab === 'natal' && <><Heading>{data.natal.affected_count ? `${data.natal.points.filter(p => p.is_mrityu_bhaga).map(p => label(p.point)).join(', ')} ${data.natal.affected_count === 1 ? 'is' : 'are'} in Mrityu Bhaga` : 'No Mrityu Bhaga found'}</Heading><Body>{data.natal.affected_count ? 'See the Mrityu Bhaga range and birth position below.' : 'None of the checked positions is inside its Mrityu Bhaga range.'}</Body><Body>Check nearby birth times</Body><View style={s.row}>{[0, 5, 10, 15].map(n => <Button key={n} active={sensitivity === n} onPress={() => {
            setSensitivity(n);
            load(false, n);
          }}>{n ? `±${n} min` : 'Recorded'}</Button>)}</View>{data.birth_time_comparison?.map(r => <Body key={r.offset_minutes}>{r.offset_minutes > 0 ? '+' : ''}{r.offset_minutes} min: {r.affected_points.map(label).join(', ') || 'No Mrityu Bhaga found'} · Lagna {r.lagna_position} · Gulika {r.gulika_position}</Body>)}{!!data.birth_time_comparison?.length && <Body style={s.muted}>Checks the recorded time, {sensitivity} minutes earlier and {sensitivity} minutes later. Times in between are not checked.</Body>}<Button onPress={() => setShowChart(!showChart)}>{showChart ? 'Hide linked chart' : 'Show linked chart'}</Button>{showChart && <View style={{
          alignItems: 'center',
          marginVertical: 12
        }}><NorthIndianChart chartData={data.natal_chart} chartType="lagna" birthData={birthData} width={300} size={300} hideInstructions highlightHouse={focusPoint?.house} highlightColor="#967631" highlightFill="rgba(150,118,49,0.15)" /></View>}{!data.natal.affected_count && <Body>None of the checked planets or points is in Mrityu Bhaga, so there are no Mrityu Bhaga dates to show.</Body>}
        {data.natal.points.filter(v => v.is_mrityu_bhaga).map(v => <Card key={v.point}><Button onPress={() => {
            setFocusPoint(v);
            setShowChart(true);
            scroll.current?.scrollTo({
              y: 0,
              animated: true
            });
          }}>Highlight H{v.house} in chart</Button><Heading>{label(v.point)} is in Mrityu Bhaga</Heading><Body>House {v.house}</Body><Body>Mrityu Bhaga range: {v.degree_span_start}°–{v.degree_span_end}° {v.sign_name}</Body><Body style={{
            fontSize: 19
          }}>{label(v.point)}’s position: {v.position}</Body><Body>Houses ruled: {v.houses_ruled.join(', ') || 'Not assigned'}</Body><Body>Sign condition: {v.dignity || 'Not applicable'}{v.retrograde === true ? ' · Retrograde' : v.retrograde === false ? ' · Direct' : ''}</Body><Body>Planet strength (Shadbala): {strength(v.strength)}</Body><Body>Combustion: {v.combustion.applicable ? v.combustion.is_combust ? 'Combust' : 'Not combust' : 'Not applicable'}</Body><Body>Sign ruler: {v.dispositor} · {v.dispositor_position} · {v.dispositor_dignity}</Body><Body>Sign ruler’s strength: {strength(v.dispositor_strength)}</Body><Body>Nakshatra: {v.nakshatra || 'Unavailable'} · {v.nakshatra_lord || ''}</Body><Body>Planet connections: {v.relationships.map(r => `${r.planet}: ${r.relation === 'same_sign' ? 'in the same sign' : `${ordinal(r.aspect_number)} aspect`}`).join(' · ') || 'None'}</Body><Body>Other charts: {Object.entries(v.divisional_placements).map(([d, p]) => `${d}: ${p.sign}, H${p.house}`).join(' · ')}</Body>{v.birth_time_sensitive && <Body style={s.muted}>A small change in birth time can change this result. Please check the birth time.</Body>}<Body style={s.muted}>Dasha at the selected start date: {data.dasha_activations.filter(r => r.point === v.point && r.start_at === data.range.start_at).map(r => links(r.connections)).join(' · ') || 'No matching dasha period'}</Body><View style={s.row}><Button onPress={() => {
              setFilter(v.point);
              setTab('calendar');
            }}>Activation dates</Button><Button onPress={() => {
              onAsk?.(`Analyze ${label(v.point)} in natal Mrityu Bhaga at ${v.position}, H${v.house}. Assess its dispositor ${v.dispositor}, strength, aspects and dasha activation, separating calculated facts from interpretation.`);
              onClose();
            }}>Ask Tara</Button></View><Note id={v.point} ready={noteReady} value={notes[v.point] || ''} onChange={value => updateNote(v.point, value)} /></Card>)}
        <Button onPress={() => setAll(!all)}>{all ? 'Hide' : 'Show'} all {data.natal.points.length} checked points</Button>{all && data.natal.points.map(v => <Card key={v.point}><Body>{label(v.point)} · {v.position}</Body><Body>{v.degree_span_start}°–{v.degree_span_end}° · {v.is_mrityu_bhaga ? 'In Mrityu Bhaga' : 'Not in Mrityu Bhaga'}</Body></Card>)}
      </>}
      {tab === 'calendar' && <><Body>Dates in birth timezone: {data?.range.timezone || birthData.timezone}. Times in {utc ? 'UTC' : 'device timezone'}.</Body><Body>From (YYYY-MM-DD)</Body><TextInput accessibilityLabel="Calendar start date" value={start} onChangeText={v => invalidate(() => setStart(v))} style={[s.input, {
          color: colors.text,
          borderColor: colors.cardBorder
        }]} /><Body>Through (YYYY-MM-DD)</Body><TextInput accessibilityLabel="Calendar end date" value={end} onChangeText={v => invalidate(() => setEnd(v))} style={[s.input, {
          color: colors.text,
          borderColor: colors.cardBorder
        }]} /><View style={s.row}>{[30, 90, 365].map(n => <Button key={n} onPress={() => {
            try {
              invalidate(() => setEnd(plus(start, n - 1)));
            } catch {
              setError('Enter a valid start date.');
            }
          }}>{n} days</Button>)}</View><Body>Choose how close a transit must be to the birth position</Body><View style={s.row}>{[.5, 1, 2, 3].map(n => <Button key={n} active={orb === n} onPress={() => invalidate(() => setOrb(n))}>±{n}°</Button>)}</View><Button active={fast} onPress={() => invalidate(() => setFast(!fast))}>Include fast planets: {fast ? 'On' : 'Off'}</Button><Button active={aspects} onPress={() => invalidate(() => setAspects(!aspects))}>Aspect degree contacts: {aspects ? 'On' : 'Off'}</Button><Button disabled={busy} active onPress={() => load(true)}>Calculate calendar</Button>
        {data?.calendar_calculated && <><View style={s.row}><Button active={filter === 'all'} onPress={() => setFilter('all')}>All points</Button>{data.natal.points.filter(v => v.is_mrityu_bhaga).map(v => <Button key={v.point} active={filter === v.point} onPress={() => setFilter(v.point)}>{label(v.point)}</Button>)}</View><View style={s.row}>{[['all', 'All evidence'], ['natal_contact', 'Longitude'], ['natal_mb_span', 'Span']].map(([key, text]) => <Button key={key} active={type === key} onPress={() => setType(key)}>{text}</Button>)}</View><Button active={multiple} onPress={() => setMultiple(!multiple)}>Show overlapping transits: {multiple ? 'On' : 'Off'}</Button><Button active={direct} onPress={() => setDirect(!direct)}>Only during the planet’s own dasha: {direct ? 'On' : 'Off'}</Button><Button active={utc} onPress={() => setUtc(!utc)}>Show UTC: {utc ? 'On' : 'Off'}</Button><Heading>Dasha activation · {dashas.length} intervals</Heading>{dashas.map((r, i) => <Card key={`${r.point}-${i}`}><Body>{label(r.point)} · {moment(r.start_at, utc)} → {moment(r.end_at, utc)}</Body><Body>{links(r.connections)}</Body></Card>)}{!dashas.length && <Body>No matching dasha period in the selected dates.</Body>}<Heading>Potential transit windows · {events.length}</Heading>{!events.length && <Body>No matching contacts in this range and filters. This does not assess other astrological factors.</Body>}{events.slice(0, visibleCount).map(r => <Card key={r.id}><Heading>{r.planet} → {label(r.point)}</Heading><Body>{kind(r)}</Body><Body style={s.muted}>Sequence in selected range: {r.sequence_motion} · Window {r.sequence_window_number} of {r.sequence_window_count}</Body><Body>{r.clipped_start ? 'Active at range start · ' : ''}{moment(r.start_at, utc)} → {moment(r.end_at, utc)}{r.clipped_end ? ' · Reaches range end' : ''}</Body>{r.exact_passes.map((v, i) => <Body key={v.at}>{r.midpoint_only ? 'Span midpoint' : 'Exact contact'} {i + 1}: {moment(v.at, utc)} · {v.motion}</Body>)}{!r.exact_passes.length && <Body>No exact {r.midpoint_only ? 'midpoint' : 'contact'} here; near-pass or clipped interval.</Body>}<Body style={s.muted}>Other bodies contacting this point during part of the window: {r.concurrent_transits?.join(', ') || 'None'}. Same-body rows count once.</Body><Body>{r.dasha_overlaps.length ? `${r.dasha_overlaps.length} dasha overlaps` : 'No direct/dispositor dasha overlap'}</Body>{r.dasha_overlaps.map((d, i) => <Body key={i} style={s.muted}>{moment(d.start_at, utc)} → {moment(d.end_at, utc)} · {links(d.connections)}</Body>)}<Button active={selected.has(r.id)} onPress={() => setSelected(prev => {
              const next = new Set(prev);
              next.has(r.id) ? next.delete(r.id) : next.add(r.id);
              return next;
            })}>{selected.has(r.id) ? 'Selected for export' : 'Select for export'}</Button><Note id={r.id} ready={noteReady} value={notes[r.id] || ''} onChange={value => updateNote(r.id, value)} /></Card>)}{events.length > visibleCount && <Button onPress={() => setVisibleCount(n => n + 40)}>Show more ({visibleCount} of {events.length})</Button>}<Button disabled={!selected.size} onPress={exportCalendar}>Export selected windows ({selected.size})</Button></>}{!data?.calendar_calculated && !busy && <Body>Calculate the calendar for these settings.</Body>}
      </>}
      {data && tab === 'audit' && <><Heading>Calculation audit</Heading><Body>{data.natal.source} · {data.natal.degree_semantics}</Body>{Object.entries(data.audit).filter(([key]) => !['sources', 'limits'].includes(key)).map(([key, value]) => <Card key={key}><Body style={{
            fontWeight: '700'
          }}>{key.replace(/_/g, ' ')}</Body><Body>{Array.isArray(value) ? value.join(', ') : String(value)}</Body></Card>)}{data.audit.limits.map(text => <Body key={text}>{text}</Body>)}<Body>Version: {data.schema_version}. No medical or mortality grade is generated.</Body><Button onPress={() => shareFile('AstroRoshni-MB-audit.json', JSON.stringify(data, null, 2), 'application/json').catch(e => Alert.alert('Export unavailable', e.message))}>Export calculation data</Button></>}
    </ScrollView>{data && <View style={s.footer}><Button disabled={exporting} onPress={exportPdf}>{exporting ? 'Preparing PDF…' : 'Export assessment PDF'}</Button></View>}
  </SafeAreaView>;
}
const s = StyleSheet.create({
  root: {
    flex: 1
  },
  header: {
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12
  },
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    paddingHorizontal: 12,
    marginVertical: 8
  },
  content: {
    padding: 16,
    paddingBottom: 32
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
    marginVertical: 6
  },
  body: {
    fontSize: 14,
    lineHeight: 22,
    marginVertical: 4
  },
  muted: {
    fontSize: 12
  },
  card: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 16,
    marginVertical: 8
  },
  button: {
    borderWidth: 1,
    borderRadius: 10,
    minHeight: 44,
    padding: 10,
    marginVertical: 3,
    alignSelf: 'flex-start'
  },
  input: {
    borderWidth: 1,
    borderRadius: 9,
    padding: 12,
    fontSize: 15
  },
  footer: {
    padding: 12,
    borderTopWidth: 1,
    borderColor: '#cbb991'
  }
});
