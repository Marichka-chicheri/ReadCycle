// Look of a drawn book: cloth colour, height and width of its spine, derived from the title so
// the same book always looks the same (on shelves, on drawn covers, in letters).

const CLOTH = [
  '#5c1724', // бордо
  '#7a2a2f', // теракотово-винний
  '#2f4a3a', // пляшкова зелень
  '#1f2f4a', // чорнильно-синій
  '#4a2340', // слива
  '#5a3a22', // тютюн
  '#3d4650', // графіт
  '#8a6a2e', // охра
  '#d9c7a3', // небілений льон
  '#2a2320', // майже чорний
];

function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function spineStyle(title = '', author = '') {
  const h = hash(`${title}|${author}`);
  const color = CLOTH[h % CLOTH.length];
  const height = 148 + ((h >> 4) % 50); // 148–197 px
  const width = 36 + ((h >> 10) % 16) + Math.min(title.length, 26) * 0.45; // ~36–64 px
  const light = color === '#d9c7a3';
  const bands = (h >> 16) % 3; // 0: none, 1: top+bottom, 2: double
  return { color, height, width: Math.round(width), light, bands };
}
