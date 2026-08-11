export const CHART_ACTIVATION_FILLS = Object.freeze({
  fully_reinforced: 'rgba(61, 107, 79, 0.20)',
  dasha_transit_activated: 'rgba(165, 18, 59, 0.16)',
  dasha_connected: 'rgba(180, 83, 9, 0.14)',
});

export function chartActivationFill(state) {
  return CHART_ACTIVATION_FILLS[state] || null;
}
