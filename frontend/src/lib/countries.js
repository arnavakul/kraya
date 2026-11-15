export const COUNTRY_CODES = [
  'IN', 'US', 'GB', 'AE', 'SG', 'CN', 'DE', 'JP', 'KR', 'FR', 'IT', 'ES', 'NL',
  'AU', 'CA', 'TH', 'VN', 'ID', 'MY', 'BD', 'LK', 'TR', 'BR', 'MX', 'ZA',
];

const names = typeof Intl.DisplayNames === 'function'
  ? new Intl.DisplayNames(['en'], { type: 'region' })
  : null;

export function countryName(code) {
  try {
    return names?.of(code) ?? code;
  } catch {
    return code;
  }
}