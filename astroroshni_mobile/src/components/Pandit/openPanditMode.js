import { Alert } from 'react-native';
import { panditAPI } from '../../services/api';

/**
 * Auth → ensure practice setup → enter pandit mode → land on Home (same tabs/menu).
 */
export async function openPanditMode({
  navigation,
  requireAuthForPaid,
  enterPanditMode,
}) {
  const authOk = await requireAuthForPaid({
    feature: 'Pandit Desk',
    message: 'Sign in to open Pandit mode and use free kundli & muhurat tools.',
    // Resume on Home (ChatScreen) — never PanditHome. PanditHome auto-enters
    // mode on mount; landing there after an unrelated Profile login felt like
    // "opening Profile turned on Pandit mode".
    resume: { resumeRoute: 'Home', resumeParams: { activatePandit: true } },
  });
  if (!authOk) return false;

  try {
    const res = await panditAPI.getMe();
    const data = res?.data || {};
    if (!data.desk_ready) {
      navigation.navigate('PanditPractice', {
        mode: 'join',
        profile: data.profile || null,
      });
      return false;
    }
    await enterPanditMode();
    navigation.navigate('Home');
    return true;
  } catch (error) {
    const detail = error?.response?.data?.detail;
    Alert.alert(
      'Pandit Desk',
      typeof detail === 'string' ? detail : (error?.message || 'Could not open Pandit mode.'),
    );
    return false;
  }
}
