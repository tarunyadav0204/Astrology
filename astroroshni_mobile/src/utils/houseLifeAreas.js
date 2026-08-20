/** Houses 1–12; labels live at premiumUi.home.houseAreas.{n} */
export const HOUSE_NUMBERS = Object.freeze([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);

export function isValidHouse(house) {
    const n = Number(house);
    return Number.isInteger(n) && n >= 1 && n <= 12;
}

/** @param {number|string} house @param {(key: string) => string} t */
export function houseLifeAreaLabel(house, t) {
    const n = Number(house);
    if (!isValidHouse(n)) return '';
    return t(`premiumUi.home.houseAreas.${n}`);
}

/** @param {{ house: number|string, score?: number }[]} items @param {(key: string) => string} t */
export function sortActivatedHousesByScore(items, t) {
    return [...items]
        .filter((item) => isValidHouse(item?.house))
        .sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0))
        .map((item) => ({
            ...item,
            house: Number(item.house),
            label: houseLifeAreaLabel(item.house, t),
        }));
}
