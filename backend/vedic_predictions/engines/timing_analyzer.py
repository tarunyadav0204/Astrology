from datetime import datetime, timedelta

class TimingAnalyzer:
    def __init__(self):
        pass
    
    def analyze_period_timing(self, period_data):
        """Analyze timing characteristics of the transit period"""
        start_date = datetime.fromisoformat(period_data['start_date'])
        end_date = datetime.fromisoformat(period_data['end_date'])
        peak_date = datetime.fromisoformat(period_data.get('peak_date', period_data['start_date']))
        now = datetime.now()
        
        timing_info = {
            'phase': self._get_timing_phase(start_date, end_date, peak_date, now),
            'duration_days': (end_date - start_date).days,
            'peak_intensity': self._calculate_peak_intensity(start_date, end_date, peak_date),
            'current_intensity': self._calculate_current_intensity(start_date, end_date, peak_date, now)
        }
        
        return timing_info
    
    def _get_timing_phase(self, start_date, end_date, peak_date, current_date):
        """Determine current phase of the transit"""
        if current_date < start_date:
            return 'approaching'
        elif current_date > end_date:
            return 'separating'
        elif abs((current_date - peak_date).days) <= 1:
            return 'peak'
        else:
            return 'active'
    
    def _calculate_peak_intensity(self, start_date, end_date, peak_date):
        """Calculate intensity at peak"""
        total_duration = (end_date - start_date).days
        if total_duration <= 1:
            return 1.0
        elif total_duration <= 7:
            return 1.2
        elif total_duration <= 30:
            return 1.0
        else:
            return 0.8
    
    def _calculate_current_intensity(self, start_date, end_date, peak_date, current_date):
        """Calculate current intensity based on position in transit"""
        if current_date < start_date or current_date > end_date:
            return 0.0
        
        total_duration = (end_date - start_date).days
        if total_duration <= 1:
            return 1.0
        
        # Distance from peak determines intensity
        days_from_peak = abs((current_date - peak_date).days)
        max_distance = max((peak_date - start_date).days, (end_date - peak_date).days)
        
        if max_distance == 0:
            return 1.0
        
        intensity = 1.0 - (days_from_peak / max_distance) * 0.5
        return max(0.3, intensity)
    
    def get_timing_description(self, timing_info, period_data):
        """Generate human-readable timing description"""
        phase = timing_info['phase']
        duration = timing_info['duration_days']
        
        descriptions = {
            'approaching': f"Building up over {duration} days",
            'active': f"Currently active for {duration} days",
            'peak': f"At peak intensity (exact on {period_data.get('peak_date', 'N/A')})",
            'separating': f"Effects diminishing after {duration}-day period"
        }
        
        return descriptions.get(phase, "Transit period active")