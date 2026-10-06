"""
Professional Festival Date Calculator using Swiss Ephemeris
Udaya-Tithi matching with sidereal lunar months (Adhika Maas aware).
"""
import swisseph as swe
from datetime import datetime, timedelta
import pytz
from .festival_data import HINDU_FESTIVALS, MONTHLY_VRATS

MONTH_NAMES = [
    "chaitra", "vaisakha", "jyeshtha", "ashadha",
    "sravana", "bhadrapada", "ashwin", "kartik",
    "margashirsha", "pausha", "magha", "phalguna",
]

MONTH_ALIASES = {
    "vaishakha": "vaisakha",
    "vaisakh": "vaisakha",
    "jyeshta": "jyeshtha",
    "jyestha": "jyeshtha",
    "ashada": "ashadha",
    "aashadha": "ashadha",
    "shravana": "sravana",
    "shravan": "sravana",
    "bhadra": "bhadrapada",
    "bhadrapad": "bhadrapada",
    "ashwina": "ashwin",
    "ashvina": "ashwin",
    "aswina": "ashwin",
    "ashwayuja": "ashwin",
    "kartika": "kartik",
    "karthik": "kartik",
    "karthika": "kartik",
    "margashira": "margashirsha",
    "margasirsha": "margashirsha",
    "agrahayana": "margashirsha",
    "pushya": "pausha",
    "pousha": "pausha",
    "pausa": "pausha",
}

# Common North-Indian / Drik named Ekadashis (Purnimanta month labels)
NAMED_EKADASHI = {
    ("chaitra", "shukla"): "Kamada Ekadashi",
    ("chaitra", "krishna"): "Papamochani Ekadashi",
    ("vaisakha", "shukla"): "Mohini Ekadashi",
    ("vaisakha", "krishna"): "Varuthini Ekadashi",
    ("jyeshtha", "shukla"): "Nirjala Ekadashi",
    ("jyeshtha", "krishna"): "Apara Ekadashi",
    ("ashadha", "shukla"): "Devshayani Ekadashi",
    ("ashadha", "krishna"): "Yogini Ekadashi",
    ("sravana", "shukla"): "Shravana Putrada Ekadashi",
    ("sravana", "krishna"): "Kamika Ekadashi",
    ("bhadrapada", "shukla"): "Parsva Ekadashi",
    ("bhadrapada", "krishna"): "Aja Ekadashi",
    ("ashwin", "shukla"): "Papankusha Ekadashi",
    ("ashwin", "krishna"): "Indira Ekadashi",
    ("kartik", "shukla"): "Prabodhini Ekadashi",
    ("kartik", "krishna"): "Rama Ekadashi",
    ("margashirsha", "shukla"): "Mokshada Ekadashi",
    ("margashirsha", "krishna"): "Utpanna Ekadashi",
    ("pausha", "shukla"): "Putrada Ekadashi",
    ("pausha", "krishna"): "Saphala Ekadashi",
    ("magha", "shukla"): "Jaya Ekadashi",
    ("magha", "krishna"): "Shattila Ekadashi",
    ("phalguna", "shukla"): "Amalaki Ekadashi",
    ("phalguna", "krishna"): "Vijaya Ekadashi",
}

# Catalog entries that are generated dynamically as monthly vrats
CATALOG_VRAT_SKIP = {
    "shukla_ekadashi",
    "krishna_ekadashi",
    "sankashti_chaturthi",
    "pradosh_vrat",
}


class FestivalCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    @staticmethod
    def normalize_month(month_name):
        if not month_name:
            return month_name
        name = str(month_name).strip().lower()
        is_adhika = name.startswith("adhika_")
        if is_adhika:
            name = name[7:]
        name = MONTH_ALIASES.get(name, name)
        return f"adhika_{name}" if is_adhika else name

    @staticmethod
    def base_month(month_name):
        name = FestivalCalculator.normalize_month(month_name)
        if name and name.startswith("adhika_"):
            return name[7:]
        return name

    def get_tithi_at_moment(self, jd):
        """Calculate exact Tithi (1-30) and Paksha at specific Julian Day"""
        # Elongation is ayanamsa-invariant; tropical positions are fine here.
        sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]

        elongation = (moon_lon - sun_lon) % 360
        tithi_float = elongation / 12
        full_tithi = int(tithi_float) + 1  # 1 to 30

        paksha = "shukla" if full_tithi <= 15 else "krishna"
        lunar_day = full_tithi if full_tithi <= 15 else full_tithi - 15

        return full_tithi, lunar_day, paksha

    def get_local_sunrise(self, jd, lat, lon):
        """Calculate local sunrise for Udaya Tithi determination"""
        try:
            res = swe.rise_trans(jd - 0.5, swe.SUN, lon, lat, 0, 0, 0, 1)
            return res[1][0] if res[0] == 0 else jd + 0.25
        except Exception:
            return jd + 0.25

    def get_local_sunset(self, jd, lat, lon):
        """Calculate local sunset for Pradosh calculations"""
        try:
            res = swe.rise_trans(jd - 0.5, swe.SUN, lon, lat, 0, 0, 0, 2)
            return res[1][0] if res[0] == 0 else jd + 0.75
        except Exception:
            return jd + 0.75

    def get_moonrise_jd(self, jd, lat, lon):
        try:
            res = swe.rise_trans(jd - 0.5, swe.MOON, lon, lat, 0, 0, 0, 1)
            if res[0] == 0:
                return res[1][0]
        except Exception:
            pass
        return None

    def get_moonrise_time(self, jd, lat, lon, timezone_name="Asia/Kolkata"):
        """Calculate moonrise time for Karwa Chauth and Sankashti Chaturthi"""
        moonrise_jd = self.get_moonrise_jd(jd, lat, lon)
        if moonrise_jd is None:
            return "Not visible"
        return self._format_local_time(moonrise_jd, timezone_name)

    def _format_local_time(self, jd_ut, timezone_name="Asia/Kolkata"):
        year, month, day, hour_utc, minute, second = swe.jdut1_to_utc(jd_ut, 1)
        utc_dt = datetime(year, month, day, int(hour_utc), int(minute), int(second), tzinfo=pytz.UTC)
        try:
            tz = pytz.timezone(timezone_name)
            local_dt = utc_dt.astimezone(tz)
            return f"{local_dt.hour:02d}:{local_dt.minute:02d}"
        except Exception:
            offset_hours = 5.5 if "Asia" in timezone_name else 0
            local_jd = jd_ut + (offset_hours / 24.0)
            year, month, day, hour, minute, second = swe.jdut1_to_utc(local_jd, 1)
            return f"{int(hour):02d}:{int(minute):02d}"

    def find_exact_new_moon_near(self, jd_guess):
        """Find exact Amavasya (sun-moon conjunction) near jd_guess."""
        lo, hi = jd_guess - 2.0, jd_guess + 2.0
        for _ in range(40):
            mid = (lo + hi) / 2.0
            sun = swe.calc_ut(mid, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon = swe.calc_ut(mid, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            elong = (moon - sun) % 360
            if elong < 180:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2.0

    def _elongation(self, jd):
        sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        return (moon - sun) % 360

    def find_surrounding_new_moons(self, jd):
        """Return (nm_start, nm_end) such that nm_start <= jd < nm_end."""
        # Walk backward to a day near conjunction (elongation near 0°)
        approx = None
        for i in range(0, 40):
            test = jd - i
            elong = self._elongation(test)
            if elong < 15 or elong > 345:
                approx = test
                break
        if approx is None:
            best_jd, best_sep = jd, 999.0
            for day in range(0, 40):
                test = jd - day
                elong = self._elongation(test)
                sep = min(elong, 360 - elong)
                if sep < best_sep:
                    best_sep = sep
                    best_jd = test
            approx = best_jd

        nm = self.find_exact_new_moon_near(approx)
        # Enforce nm_start <= jd < nm_end
        guard = 0
        while nm > jd and guard < 3:
            nm = self.find_exact_new_moon_near(nm - 29.53059)
            guard += 1

        nxt = self.find_exact_new_moon_near(nm + 29.53059)
        if nxt <= nm + 20:
            nxt = self.find_exact_new_moon_near(nm + 30.5)

        guard = 0
        while nxt <= jd and guard < 3:
            nm = nxt
            nxt = self.find_exact_new_moon_near(nm + 29.53059)
            if nxt <= nm + 20:
                nxt = self.find_exact_new_moon_near(nm + 30.5)
            guard += 1

        return nm, nxt

    def get_lunar_month_with_adhika(self, jd, calendar_system="purnimanta"):
        """
        Sidereal Amanta month naming with Adhika Maas.
        Month beginning at new moon N is named from sidereal sun sign at N using (sign+1)%12.
        Adhika when consecutive new moons keep the same sidereal sun sign.
        Purnimanta: Krishna paksha uses the next Amanta month name (Drik North-India style).
        """
        nm_start, nm_end = self.find_surrounding_new_moons(jd)
        sun_start = swe.calc_ut(nm_start, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        sun_end = swe.calc_ut(nm_end, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        sign_start = int(sun_start / 30) % 12
        sign_end = int(sun_end / 30) % 12
        is_adhika = sign_start == sign_end

        month_index = (sign_start + 1) % 12
        month_name = MONTH_NAMES[month_index]
        if is_adhika:
            month_name = f"adhika_{month_name}"

        if calendar_system == "purnimanta":
            _, _, paksha = self.get_tithi_at_moment(jd)
            if paksha == "krishna":
                next_index = (month_index + 1) % 12
                # Keep Adhika label only for the amanta adhika month itself;
                # purnimanta Krishna advances into the following named month.
                month_name = MONTH_NAMES[next_index]

        return month_name, is_adhika

    def get_lunar_month_simple(self, jd, calendar_system="purnimanta"):
        return self.get_lunar_month_with_adhika(jd, calendar_system)[0]

    def is_adhika_month(self, year, month):
        """Check if given Gregorian month contains an Adhika lunar month"""
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        current_date = start_date
        while current_date < end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day, 12)
            _, is_adhika = self.get_lunar_month_with_adhika(jd)
            if is_adhika:
                return True
            current_date += timedelta(days=7)
        return False

    def get_tithi_end_time(self, jd_start, target_tithi, lat, lon, timezone_name="Asia/Kolkata"):
        """Calculate exact moment when tithi ends in proper timezone"""
        jd = jd_start
        max_search_hours = 48

        for minute in range(int(max_search_hours * 60)):
            jd_test = jd + (minute / (24 * 60))
            sun_lon = swe.calc_ut(jd_test, swe.SUN)[0][0]
            moon_lon = swe.calc_ut(jd_test, swe.MOON)[0][0]
            elongation = (moon_lon - sun_lon) % 360
            current_tithi = int(elongation / 12) + 1

            if current_tithi != target_tithi:
                return self._format_local_time(jd_test, timezone_name)
        return "Next Day"

    def calculate_parana_time(self, jd_ekadashi, lat, lon, timezone_name="Asia/Kolkata"):
        """Calculate proper Ekadashi Parana time avoiding Hari Vasara"""
        jd_next_day = jd_ekadashi + 1
        jd_next_sunrise = self.get_local_sunrise(jd_next_day, lat, lon)

        full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd_next_sunrise)

        if lunar_day == 12:  # Dwadashi present at sunrise
            dwadashi_start = jd_next_sunrise
            dwadashi_end_jd = None
            for minute in range(48 * 60):
                test_jd = dwadashi_start + (minute / (24 * 60))
                _, test_lunar_day, _ = self.get_tithi_at_moment(test_jd)
                if test_lunar_day != 12:
                    dwadashi_end_jd = test_jd
                    break

            if dwadashi_end_jd:
                dwadashi_duration = dwadashi_end_jd - dwadashi_start
                hari_vasara_end = dwadashi_start + (dwadashi_duration * 0.25)
                return f"After {self._format_local_time(hari_vasara_end, timezone_name)} (avoiding Hari Vasara)"

        return f"After {self._format_local_time(jd_next_sunrise, timezone_name)}"

    def _month_matches(self, festival_month, lunar_month, paksha, calendar_system):
        festival_month = self.normalize_month(festival_month)
        lunar_month = self.normalize_month(lunar_month)
        if not festival_month or festival_month == "all":
            return True

        fest_base = self.base_month(festival_month)
        lunar_base = self.base_month(lunar_month)
        if fest_base == lunar_base:
            return True

        # Catalog months are North-Indian / Purnimanta labels.
        # Under Amanta, Krishna-paksha of Purnimanta month M = Amanta month M-1.
        if calendar_system == "amanta" and paksha == "krishna":
            try:
                idx = MONTH_NAMES.index(fest_base)
                if lunar_base == MONTH_NAMES[(idx - 1) % 12]:
                    return True
            except ValueError:
                pass

        return False

    def _inferred_paksha(self, festival):
        if festival.get("paksha"):
            return festival["paksha"]
        lunar_day = festival.get("lunar_day")
        if lunar_day == "purnima":
            return "shukla"
        if lunar_day == "amavasya":
            return "krishna"
        return None

    def find_festival_dates(
        self,
        year,
        month=None,
        lat=28.6139,
        lon=77.2090,
        calendar_system="purnimanta",
        timezone_name="Asia/Kolkata",
    ):
        """Find festivals with geographic precision and Adhika Maas support"""
        festivals = []
        start_date = datetime(year, month or 1, 1)

        if month:
            end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        else:
            end_date = datetime(year + 1, 1, 1)

        current_date = start_date
        while current_date < end_date:
            jd_midnight = swe.julday(current_date.year, current_date.month, current_date.day, 0)
            jd_sunrise = self.get_local_sunrise(jd_midnight, lat, lon)

            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd_sunrise)
            lunar_month, is_adhika = self.get_lunar_month_with_adhika(jd_sunrise, calendar_system)
            tithi_end_time = self.get_tithi_end_time(jd_sunrise, full_tithi, lat, lon, timezone_name)

            for festival_id, festival in HINDU_FESTIVALS.items():
                if festival_id in CATALOG_VRAT_SKIP:
                    continue

                if self._matches_pro_logic(
                    festival,
                    festival_id,
                    full_tithi,
                    lunar_day,
                    paksha,
                    lunar_month,
                    current_date,
                    jd_sunrise,
                    lat,
                    lon,
                    calendar_system,
                ):
                    festival_data = {
                        "id": festival_id,
                        "name": festival["name"],
                        "date": current_date.strftime("%Y-%m-%d"),
                        "tithi_at_sunrise": full_tithi,
                        "tithi_end_time": tithi_end_time,
                        "paksha": paksha,
                        "lunar_month": lunar_month,
                        "is_adhika_month": is_adhika,
                        "type": festival["type"],
                        "description": festival["description"],
                        "significance": festival["significance"],
                        "rituals": festival["rituals"],
                    }

                    if (
                        "fast" in festival.get("name", "").lower()
                        or "vrat" in festival.get("name", "").lower()
                        or lunar_day == 11
                        or festival.get("has_moonrise")
                    ):
                        festival_data["parana_time"] = self.calculate_parana_time(
                            jd_sunrise, lat, lon, timezone_name
                        )

                    if festival.get("has_moonrise") or festival_id in ("karva_chauth", "sankashti_chaturthi"):
                        festival_data["moonrise_time"] = self.get_moonrise_time(
                            jd_sunrise, lat, lon, timezone_name
                        )

                    festivals.append(festival_data)

            current_date += timedelta(days=1)

        return sorted(festivals, key=lambda x: x["date"])

    def _matches_pro_logic(
        self,
        festival,
        festival_id,
        full_tithi,
        lunar_day,
        paksha,
        lunar_month,
        date,
        jd_sunrise,
        lat,
        lon,
        calendar_system="purnimanta",
    ):
        """Professional matching with Udaya Tithi and time-window logic"""
        _, is_adhika = self.get_lunar_month_with_adhika(jd_sunrise, calendar_system)

        # Prevent major festivals in Adhika (leap) months
        if is_adhika and festival.get("type") == "major_festival":
            return False

        # Multi-day / special lunar spans handled explicitly
        if festival.get("lunar_day") == "purnima_to_amavasya":
            return self._match_pitra_paksha(festival, lunar_day, paksha, lunar_month, calendar_system)

        if festival.get("lunar_day") == "saptami_to_dashami":
            return (
                self._month_matches(festival.get("month"), lunar_month, paksha, calendar_system)
                and paksha == "shukla"
                and lunar_day in (7, 8, 9, 10)
            )

        # Solar festivals
        if "solar_date" in festival:
            solar = festival["solar_date"]
            if solar == "january_14" and date.month == 1 and date.day == 14:
                return True
            if solar == "april_13" and date.month == 4 and date.day == 13:
                return True
            if solar == "april_14" and date.month == 4 and date.day == 14:
                return True
            return False

        if "lunar_day" not in festival:
            return False

        day_map = {
            "pratipada": 1, "dvitiya": 2, "tritiya": 3, "chaturthi": 4, "panchami": 5,
            "shashthi": 6, "saptami": 7, "ashtami": 8, "navami": 9, "dashami": 10,
            "ekadashi": 11, "dvadashi": 12, "trayodashi": 13, "chaturdashi": 14,
            "purnima": 15, "amavasya": 15,
        }

        target_lunar_day = day_map.get(festival["lunar_day"])
        if not target_lunar_day:
            return False

        if not self._month_matches(festival.get("month"), lunar_month, paksha, calendar_system):
            return False

        required_paksha = self._inferred_paksha(festival)
        if required_paksha and required_paksha != paksha:
            return False
        # Safety: never match purnima/amavasya without paksha alignment
        if festival["lunar_day"] == "purnima" and paksha != "shukla":
            return False
        if festival["lunar_day"] == "amavasya" and paksha != "krishna":
            return False

        jd_sunset = self.get_local_sunset(jd_sunrise, lat, lon)

        # Special window checks (may override strict Udaya equality)
        if festival_id == "diwali":
            jd_pradosh = jd_sunset + (2.4 / 24.0)
            _, pradosh_day, pradosh_paksha = self.get_tithi_at_moment(jd_pradosh)
            return pradosh_day == 15 and pradosh_paksha == "krishna"

        if festival_id == "maha_shivratri":
            # Nishita Kaal: Krishna Chaturdashi near local midnight
            jd_midnight = jd_sunrise + 0.5
            _, midnight_day, midnight_paksha = self.get_tithi_at_moment(jd_midnight)
            return midnight_day == 14 and midnight_paksha == "krishna"

        if festival_id == "janmashtami":
            jd_midnight = jd_sunrise + 0.5
            _, midnight_day, midnight_paksha = self.get_tithi_at_moment(jd_midnight)
            return midnight_day == 8 and midnight_paksha == "krishna"

        if festival_id == "holika_dahan":
            # Prefer Udaya Purnima (common panchang listing day)
            return lunar_day == 15 and paksha == "shukla"

        if festival_id == "karva_chauth":
            if not (lunar_day == 4 and paksha == "krishna"):
                return False
            moonrise_jd = self.get_moonrise_jd(jd_sunrise, lat, lon)
            if moonrise_jd is None:
                return True
            _, mr_day, mr_paksha = self.get_tithi_at_moment(moonrise_jd)
            return mr_day == 4 and mr_paksha == "krishna"

        if festival_id == "ram_navami":
            # Madhyahna rule: Navami should prevail around midday
            jd_mid = jd_sunrise + 0.5 * (jd_sunset - jd_sunrise)
            _, mid_day, mid_paksha = self.get_tithi_at_moment(jd_mid)
            return mid_day == 9 and mid_paksha == "shukla"

        if festival_id == "dussehra":
            # Aparahna rule commonly used for Vijayadashami
            jd_aparahna = jd_sunrise + 0.6 * (jd_sunset - jd_sunrise)
            _, ap_day, ap_paksha = self.get_tithi_at_moment(jd_aparahna)
            return ap_day == 10 and ap_paksha == "shukla"

        if festival_id == "akshaya_tritiya":
            # Prefer midday Tritiya when Udaya differs by a day
            jd_mid = jd_sunrise + 0.5 * (jd_sunset - jd_sunrise)
            _, mid_day, mid_paksha = self.get_tithi_at_moment(jd_mid)
            return mid_day == 3 and mid_paksha == "shukla"

        # Short / Kshaya Purnima: tithi may not prevail at sunrise
        if festival.get("lunar_day") == "purnima":
            if lunar_day == 15 and paksha == "shukla":
                return True
            if lunar_day == 14 and paksha == "shukla":
                for step in range(1, 48):
                    _, d, p = self.get_tithi_at_moment(jd_sunrise + (step / 48.0))
                    if d == 15 and p == "shukla":
                        return True
            return False

        # Standard Udaya Tithi
        return target_lunar_day == lunar_day

    def _match_pitra_paksha(self, festival, lunar_day, paksha, lunar_month, calendar_system):
        if paksha != "krishna":
            return False
        # Pitru Paksha: Krishna pratipada through amavasya before Sharad Navratri.
        # Purnimanta label: Ashwin Krishna. Amanta label: Bhadrapada Krishna.
        if calendar_system == "purnimanta":
            return self.base_month(lunar_month) == "ashwin"
        return self._month_matches(festival.get("month", "bhadrapada"), lunar_month, paksha, calendar_system)

    def get_monthly_vrats(
        self,
        year,
        month,
        lat=28.6139,
        lon=77.2090,
        calendar_system="purnimanta",
        timezone_name="Asia/Kolkata",
    ):
        """Get monthly vrats with dynamic generation, timezone and Adhika support"""
        vrats = []
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        vrat_types = {
            11: {
                "shukla": {"name": "Shukla Ekadashi", "id": "shukla_ekadashi", "has_parana": True},
                "krishna": {"name": "Krishna Ekadashi", "id": "krishna_ekadashi", "has_parana": True},
            },
            13: {
                "shukla": {"name": "Shukla Pradosh Vrat", "id": "shukla_pradosh", "has_parana": True, "pradosh_window": True},
                "krishna": {"name": "Krishna Pradosh Vrat", "id": "krishna_pradosh", "has_parana": True, "pradosh_window": True},
            },
            4: {
                "krishna": {"name": "Sankashti Chaturthi", "id": "sankashti_chaturthi", "has_moonrise": True, "has_parana": True},
                "shukla": {"name": "Vinayaka Chaturthi", "id": "vinayaka_chaturthi", "has_parana": True},
            },
            14: {
                "krishna": {"name": "Masik Shivaratri", "id": "masik_shivaratri", "has_parana": True},
            },
            15: {
                "shukla": {"name": "Purnima Vrat", "id": "purnima_vrat", "has_parana": True},
                "krishna": {"name": "Amavasya Vrat", "id": "amavasya_vrat", "has_parana": True},
            },
        }

        found_vrat_types = set()
        current_lunar_month = None
        current_date = start_date

        while current_date < end_date:
            jd_midnight = swe.julday(current_date.year, current_date.month, current_date.day, 0)
            jd_sunrise = self.get_local_sunrise(jd_midnight, lat, lon)

            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd_sunrise)
            lunar_month, _ = self.get_lunar_month_with_adhika(jd_sunrise, calendar_system)
            date_str = current_date.strftime("%Y-%m-%d")

            if current_lunar_month != lunar_month:
                current_lunar_month = lunar_month
                found_vrat_types = set()

            if lunar_day in vrat_types and paksha in vrat_types[lunar_day]:
                vrat_def = vrat_types[lunar_day][paksha]
                vrat_type_key = f"{lunar_month}_{vrat_def['id']}"

                # Pradosh: require Trayodashi during Pradosh Kaal (sunset + ~2.4h)
                if vrat_def.get("pradosh_window"):
                    jd_sunset = self.get_local_sunset(jd_sunrise, lat, lon)
                    _, p_day, p_paksha = self.get_tithi_at_moment(jd_sunset + (2.4 / 24.0))
                    if not (p_day == 13 and p_paksha == paksha):
                        current_date += timedelta(days=1)
                        continue

                # Sankashti: prefer Chaturthi at moonrise when available
                if vrat_def["id"] == "sankashti_chaturthi":
                    moonrise_jd = self.get_moonrise_jd(jd_sunrise, lat, lon)
                    if moonrise_jd is not None:
                        _, mr_day, mr_paksha = self.get_tithi_at_moment(moonrise_jd)
                        if not (mr_day == 4 and mr_paksha == "krishna"):
                            current_date += timedelta(days=1)
                            continue

                if vrat_type_key not in found_vrat_types:
                    found_vrat_types.add(vrat_type_key)
                    tithi_end_time = self.get_tithi_end_time(jd_sunrise, full_tithi, lat, lon, timezone_name)

                    display_name = vrat_def["name"]
                    if vrat_def["id"] in ("shukla_ekadashi", "krishna_ekadashi"):
                        named = NAMED_EKADASHI.get((self.base_month(lunar_month), paksha))
                        if named:
                            display_name = named

                    vrat_data = {
                        "id": vrat_def["id"],
                        "name": display_name,
                        "date": date_str,
                        "type": "vrat",
                        "tithi_at_sunrise": full_tithi,
                        "tithi_end_time": tithi_end_time,
                        "paksha": paksha,
                        "lunar_month": lunar_month,
                    }

                    if vrat_def.get("has_parana"):
                        vrat_data["parana_time"] = self.calculate_parana_time(
                            jd_sunrise, lat, lon, timezone_name
                        )
                    if vrat_def.get("has_moonrise"):
                        vrat_data["moonrise_time"] = self.get_moonrise_time(
                            jd_sunrise, lat, lon, timezone_name
                        )

                    vrats.append(vrat_data)

            current_date += timedelta(days=1)

        return sorted(vrats, key=lambda x: x["date"])
