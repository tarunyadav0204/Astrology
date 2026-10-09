import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Switch, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import PlaceSearchField from '../PlaceSearchField';
import WebDatePickerModal from '../Common/WebDatePickerModal';
const isoDate = date => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
export default function MuhuratSetup({ initial = {}, onSubmit }) {
  const { colors } = useTheme(), { t } = useTranslation();
  const [draft, setDraft] = useState({ allowed_start: '08:00', allowed_end: '18:00', minimum_duration_minutes: 15, personalized: false, ...initial });
  const [picker, setPicker] = useState(null), [error, setError] = useState('');
  const label = key => t(`premiumUi.chat.muhurat.${key}`);
  const update = (key,value) => setDraft(old => ({ ...old, [key]:value }));
  const button = { padding: 12, marginVertical: 6, borderRadius: 12, borderWidth: 1, borderColor: colors.cardBorder, backgroundColor: colors.surfaceRaised };
  const text = { color: colors.text };
  const submit = () => {
    if (!draft.event_type || !draft.location || !draft.start_date || !draft.end_date || draft.end_date < draft.start_date || (Date.parse(draft.end_date)-Date.parse(draft.start_date))/86400000 >=60 || !/^\d{2}:\d{2}$/.test(draft.allowed_start) || !/^\d{2}:\d{2}$/.test(draft.allowed_end) || draft.allowed_end <= draft.allowed_start) { setError(label('invalid')); return; }
    onSubmit(draft);
  };
  const pickerValue = draft[picker] ? new Date(`${draft[picker]}T12:00:00`) : new Date();
  return <ScrollView keyboardShouldPersistTaps="handled"><Text style={text}>{label('description')}</Text>
    <Text style={[text,{ fontWeight:'700', marginTop:16 }]}>{label('activity')}</Text>
    {['vehicle','home','gold','business'].map(id => <TouchableOpacity key={id} accessibilityRole="radio" accessibilityState={{ selected:draft.event_type===id }} style={[button, draft.event_type===id && { borderColor:colors.primary }]} onPress={() => update('event_type',id)}><Text style={text}>{label(id)}</Text></TouchableOpacity>)}
    {draft.event_type && !['vehicle','home','gold','business'].includes(draft.event_type) && <Text style={text}>{draft.event_type} · {label('limited')}</Text>}
    <Text style={[text,{ fontWeight:'700', marginVertical:12 }]}>{label('eventCity')}</Text>
    <PlaceSearchField selectedName={draft.location?.name || ''} onSelect={place => update('location',{ name:place.name, latitude:Number(place.latitude), longitude:Number(place.longitude), timezone:String(place.timezone || 'UTC') })} placeholder={label('cityPlaceholder')} />
    {['start_date','end_date'].map(key => <TouchableOpacity key={key} style={button} onPress={() => setPicker(key)}><Text style={text}>{label(key)}: {draft[key] || label('selectDate')}</Text></TouchableOpacity>)}
    {['allowed_start','allowed_end','check_time'].map(key => <View key={key}><Text style={text}>{label(key)}</Text><TextInput accessibilityLabel={label(key)} style={[button,text]} value={draft[key] || ''} placeholder="HH:MM" placeholderTextColor={colors.textMuted} onChangeText={value => update(key,value)} /></View>)}
    <View style={{ flexDirection:'row', alignItems:'center', marginVertical:12 }}><Switch value={draft.personalized} onValueChange={value => update('personalized',value)} /><Text style={[text,{ flex:1, marginLeft:12 }]}>{label('personalized')}</Text></View>
    <Text style={text}>{label('coverage')}</Text>{error && <Text accessibilityRole="alert" style={text}>{error}</Text>}
    <TouchableOpacity accessibilityRole="button" style={button} onPress={submit}><Text style={[text,{fontWeight:'700'}]}>{label('submit')}</Text></TouchableOpacity>
    {picker && Platform.OS!=='web' && <DateTimePicker mode="date" value={pickerValue} onChange={(event,date) => { const key=picker; setPicker(null); if(date && event.type!=='dismissed') update(key,isoDate(date)); }} />}
    {Platform.OS==='web' && <WebDatePickerModal visible={Boolean(picker)} value={pickerValue} onClose={() => setPicker(null)} onChange={date => { if(picker) update(picker,isoDate(date)); setPicker(null); }} />}
  </ScrollView>;
}
