import { useTranslation } from 'react-i18next';

export const useAstrologyTranslation = () => {
  const { t, i18n } = useTranslation();

  const translatePlanet = (planet) => {
    return t(`planets.${planet}`, planet);
  };

  const translateSign = (sign) => {
    return t(`signs.${sign}`, sign);
  };

  const translateNakshatra = (nakshatra) => {
    return t(`nakshatras.${nakshatra}`, nakshatra);
  };

  return {
    t,
    i18n,
    translatePlanet,
    translateSign,
    translateNakshatra,
  };
};
