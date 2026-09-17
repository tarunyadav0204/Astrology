import React, { useEffect, useRef, useState } from 'react';
import {
  Keyboard,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import { resolvePlace, searchPlaces } from '../services/placeSearch';

export default function PlaceSearchField({
  selectedName = '',
  selectedLatitude,
  selectedLongitude,
  onSelect,
  onDraftChange,
  placeholder,
}) {
  const { t } = useTranslation();
  const { colors, getCardElevation } = useTheme();
  const [query, setQuery] = useState(selectedName || '');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchTimeoutRef = useRef(null);
  const hasCoords = Number.isFinite(parseFloat(selectedLatitude)) && Number.isFinite(parseFloat(selectedLongitude));

  useEffect(() => {
    setQuery((current) => (selectedName && selectedName !== current ? selectedName : current));
  }, [selectedName]);

  useEffect(() => () => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
  }, []);

  const fieldSurface = { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder };
  const selectedSurface = { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder };
  const glassElevation = Platform.OS === 'android'
    ? null
    : { elevation: getCardElevation ? getCardElevation(10) : 8 };

  const handleChange = (value) => {
    setQuery(value);
    onDraftChange?.(value);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(async () => {
      if (value.trim().length < 3) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }
      const results = await searchPlaces(value);
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
    }, 300);
  };

  const handleSelect = async (suggestion) => {
    setShowSuggestions(false);
    setSuggestions([]);
    setTimeout(() => Keyboard.dismiss(), 100);
    const resolved = await resolvePlace(suggestion);
    if (!resolved) return;
    setQuery(resolved.name);
    onSelect?.(resolved);
  };

  return (
    <View>
      <View style={styles.locationInputWrapper}>
        <TextInput
          style={[styles.input, fieldSurface, { color: colors.text }]}
          value={query}
          onChangeText={handleChange}
          placeholder={placeholder || t('birthForm.placePlaceholder', 'City, State, Country')}
          placeholderTextColor={colors.textSecondary}
          autoCorrect={false}
          onBlur={() => {
            setTimeout(() => setShowSuggestions(false), 200);
          }}
          onFocus={() => {
            if (suggestions.length > 0) setShowSuggestions(true);
          }}
        />
        {showSuggestions && suggestions.length > 0 ? (
          <ScrollView
            style={[styles.suggestionsList, fieldSurface, glassElevation]}
            contentContainerStyle={styles.suggestionsListContent}
            keyboardShouldPersistTaps="always"
            nestedScrollEnabled
            showsVerticalScrollIndicator
            bounces={false}
          >
            {suggestions.map((suggestion) => (
              <TouchableOpacity
                key={suggestion.id}
                style={[styles.suggestionItem, { borderBottomColor: colors.cardBorder }]}
                onPress={() => handleSelect(suggestion)}
                activeOpacity={0.7}
              >
                <Text style={[styles.suggestionText, { color: colors.text }]} numberOfLines={2}>
                  📍 {suggestion.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        ) : null}
      </View>
      {hasCoords ? (
        <View style={[styles.locationDetails, selectedSurface]}>
          <Text style={[styles.locationDetailsTitle, { color: colors.text }]}>
            📍 {t('birthForm.selectedLocation', 'Selected Location')}
          </Text>
          <Text style={[styles.locationDetailsText, { color: colors.text }]}>{selectedName || query}</Text>
          <View style={[styles.coordinatesRow, { borderTopColor: colors.selectionBorder }]}>
            <Text style={[styles.coordinateText, { color: colors.textSecondary }]}>
              {t('birthForm.coords.lat', 'Lat:')} {parseFloat(selectedLatitude).toFixed(4)}
            </Text>
            <Text style={[styles.coordinateText, { color: colors.textSecondary }]}>
              {t('birthForm.coords.long', 'Long:')} {parseFloat(selectedLongitude).toFixed(4)}
            </Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  locationInputWrapper: {
    position: 'relative',
    zIndex: 20,
  },
  input: {
    borderWidth: 1,
    borderRadius: 18,
    minHeight: 60,
    paddingHorizontal: 18,
    paddingVertical: 14,
    fontSize: 17,
    textAlign: 'left',
    ...(Platform.OS === 'web'
      ? { outlineStyle: 'none', outlineWidth: 0, boxShadow: 'none' }
      : null),
  },
  suggestionsList: {
    maxHeight: 220,
    borderRadius: 12,
    marginTop: 8,
    overflow: 'hidden',
    borderWidth: 1,
  },
  suggestionsListContent: {
    flexGrow: 1,
    paddingBottom: 8,
  },
  suggestionItem: {
    padding: 16,
    borderBottomWidth: 1,
  },
  suggestionText: {
    fontSize: 14,
  },
  locationDetails: {
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
  },
  locationDetailsTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  locationDetailsText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  coordinatesRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
  },
  coordinateText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
