import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Switch, Platform, Modal } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { selectedRitualValue, initializeMuhuratDraft } from '../../utils/festivalPujaSelection';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import festivalCatalog from '../../data/festivalPujaCatalog.json';
import PlaceSearchField from '../PlaceSearchField';
import { SafeAreaView } from 'react-native-safe-area-context';
import WebDatePickerModal from '../Common/WebDatePickerModal';
const isoDate = date => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
export default function MuhuratSetup({ initial = {}, onSubmit }) {
  const { colors } = useTheme(), { t } = useTranslation();
  const [draft, setDraft] = useState(() => initializeMuhuratDraft(initial, festivalCatalog));
  const initialKey = JSON.stringify(initial);
  useEffect(() => { setDraft(initializeMuhuratDraft(JSON.parse(initialKey), festivalCatalog)); }, [initialKey]);
  const festival = draft.event_type === 'festival_puja' || Boolean(draft.festival_id);
  const selectedFestival = festivalCatalog.find(item => item.id === draft.festival_id);
  const ritualValue = selectedRitualValue(selectedFestival, draft.ritual);
  const ritualOptions = selectedFestival?.ritual_options || [];
  const [festivalSearch, setFestivalSearch] = useState('');
  const [locationPickerOpen, setLocationPickerOpen] = useState(false);
  const [picker, setPicker] = useState(null), [error, setError] = useState('');
  const label = key => t(`premiumUi.chat.muhurat.${key}`);
  const update = (key,value) => setDraft(old => ({ ...old, [key]:value }));
  const button = { padding: 12, marginVertical: 6, borderRadius: 12, borderWidth: 1, borderColor: colors.cardBorder, backgroundColor: colors.surfaceRaised };
  const text = { color: colors.text };
  const submit = () => {
    if (!draft.event_type || !draft.location || !draft.start_date || !draft.end_date || draft.end_date < draft.start_date || (Date.parse(draft.end_date)-Date.parse(draft.start_date))/86400000 >= (festival ? 366 : 60) || (festival && (!draft.festival_id || Number((draft.start_date || '').slice(0,4)) < 1900 || Number((draft.start_date || '').slice(0,4)) > 2100)) || !/^\d{2}:\d{2}$/.test(draft.allowed_start) || !/^\d{2}:\d{2}$/.test(draft.allowed_end) || draft.allowed_end <= draft.allowed_start) { setError(label(festival ? 'festivalInvalid' : 'invalid')); return; }
    onSubmit(draft);
  };
  const pickerValue = draft[picker] ? new Date(`${draft[picker]}T12:00:00`) : new Date();
  return <ScrollView keyboardShouldPersistTaps="handled" keyboardDismissMode="none" nestedScrollEnabled><Text style={text}>{label(festival ? 'festivalDescription' : 'description')}</Text>
    <Text style={[text,{ fontWeight:'700', marginTop:16 }]}>{label('activity')}</Text>
    {['vehicle','home','gold','business','festival_puja'].map(id => <TouchableOpacity key={id} accessibilityRole="radio" accessibilityState={{ selected:draft.event_type===id }} style={[button, draft.event_type===id && { borderColor:colors.primary }]} onPress={() => setDraft(old => ({...old,event_type:id,festival_id:null,ritual:null,...(id==='festival_puja' ? {allowed_start:'00:00',allowed_end:'23:59',festival_year:new Date().getFullYear(),start_date:`${new Date().getFullYear()}-01-01`,end_date:`${new Date().getFullYear()}-12-31`} : {})}))}><Text style={text}>{label(id)}</Text></TouchableOpacity>)}
    {draft.event_type && !['vehicle','home','gold','business','festival_puja'].includes(draft.event_type) && <Text style={text}>{draft.event_type}</Text>}
    {festival && <>
      <Text style={[text,{fontWeight:'700',marginTop:12}]}>{label('festival')}</Text>
      {selectedFestival && <Text style={text}>{selectedFestival.name}</Text>}
      <TextInput accessibilityLabel={label('festival')} style={[button,text]} value={festivalSearch} onChangeText={setFestivalSearch} placeholder={label('searchFestival')} placeholderTextColor={colors.textMuted} />
      {festivalSearch.trim().length > 1 && festivalCatalog.filter(item => item.name.toLowerCase().includes(festivalSearch.trim().toLowerCase())).map(item => <TouchableOpacity key={item.id} style={button} onPress={() => {setDraft(old=>({...old,festival_id:item.id,ritual:null}));setFestivalSearch('');}}><Text style={text}>{item.name}</Text></TouchableOpacity>)}
      <Text style={text}>{label('year')}</Text>
      <View style={button}><Picker accessibilityLabel={label('year')} selectedValue={Number(draft.festival_year || (draft.start_date || '').slice(0,4)) || new Date().getFullYear()} dropdownIconColor={colors.text} style={text} onValueChange={value => { const year=Number(value); setDraft(old=>({...old,festival_year:year,start_date:`${year}-01-01`,end_date:`${year}-12-31`})); }}>
        {Array.from({length:201},(_,index)=>1900+index).map(year=><Picker.Item key={year} value={year} label={String(year)} color={colors.text} />)}
      </Picker></View>
      {selectedFestival && !selectedFestival.ritual && <Text style={text}>{label('timingUnavailable')}</Text>}
      <Text style={text}>{label('ritual')}</Text>
      <View style={button}><Picker accessibilityLabel={label('ritual')} selectedValue={ritualValue} dropdownIconColor={colors.text} style={text} onValueChange={value=>update('ritual',value || null)}>
        {!ritualOptions.length && <Picker.Item label={label(selectedFestival ? 'timingUnavailable' : 'chooseFestivalFirst')} value="" color={colors.text} />}
        {ritualOptions.map(item => <Picker.Item key={item.value} value={item.value} enabled={item.supported} color={colors.text} label={`${item.label}${item.supported ? '' : ` · ${label('timingUnavailable')}`}`} />)}
        {ritualValue && !ritualOptions.some(item=>item.value===ritualValue) && <Picker.Item value={ritualValue} label={String(draft.ritual)} color={colors.text} />}
      </Picker></View>
    </>}
    <Text style={[text,{ fontWeight:'700', marginVertical:12 }]}>{label('eventCity')}</Text>
    <TouchableOpacity accessibilityRole="button" accessibilityLabel={label('eventCity')} style={button} onPress={() => setLocationPickerOpen(true)}>
      <Text style={text}>{draft.location?.name || label('cityPlaceholder')}</Text>
    </TouchableOpacity>
    <Modal visible={locationPickerOpen} animationType="slide" onRequestClose={() => setLocationPickerOpen(false)}>
      <SafeAreaView style={{flex:1, backgroundColor:colors.background}}>
        <View style={{padding:20, flex:1}}>
          <View style={{flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:16}}>
            <Text style={[text,{fontWeight:'700',fontSize:20,flex:1}]}>{label('eventCity')}</Text>
            <TouchableOpacity accessibilityRole="button" accessibilityLabel={t('common.close', 'Close')} onPress={() => setLocationPickerOpen(false)} style={button}><Text style={text}>✕</Text></TouchableOpacity>
          </View>
          <PlaceSearchField selectedName={draft.location?.name || ''} selectedLatitude={draft.location?.latitude} selectedLongitude={draft.location?.longitude} onSelect={place => {
            update('location', {name:place.name, latitude:Number(place.latitude), longitude:Number(place.longitude), timezone:String(place.timezone || 'UTC')});
            setError('');
            setLocationPickerOpen(false);
          }} placeholder={label('cityPlaceholder')} />
        </View>
      </SafeAreaView>
    </Modal>
    {(!festival ? ['start_date','end_date'] : []).map(key => <TouchableOpacity key={key} style={button} onPress={() => setPicker(key)}><Text style={text}>{label(key)}: {draft[key] || label('selectDate')}</Text></TouchableOpacity>)}
    {(!festival ? ['allowed_start','allowed_end','check_time'] : []).map(key => <View key={key}><Text style={text}>{label(key)}</Text><TextInput accessibilityLabel={label(key)} style={[button,text]} value={draft[key] || ''} placeholder="HH:MM" placeholderTextColor={colors.textMuted} onChangeText={value => update(key,value)} /></View>)}
    <View style={{ flexDirection:'row', alignItems:'center', marginVertical:12 }}><Switch value={draft.personalized} onValueChange={value => update('personalized',value)} /><Text style={[text,{ flex:1, marginLeft:12 }]}>{label('personalized')}</Text></View>
    <Text style={text}>{label(festival ? 'pujaCityHint' : 'coverage')}</Text>{error && <Text accessibilityRole="alert" style={text}>{error}</Text>}
    <TouchableOpacity accessibilityRole="button" style={button} onPress={submit}><Text style={[text,{fontWeight:'700'}]}>{label('submit')}</Text></TouchableOpacity>
    {picker && Platform.OS!=='web' && <DateTimePicker mode="date" value={pickerValue} onChange={(event,date) => { const key=picker; setPicker(null); if(date && event.type!=='dismissed') update(key,isoDate(date)); }} />}
    {Platform.OS==='web' && <WebDatePickerModal visible={Boolean(picker)} value={pickerValue} onClose={() => setPicker(null)} onChange={date => { if(picker) update(picker,isoDate(date)); setPicker(null); }} />}
  </ScrollView>;
}
