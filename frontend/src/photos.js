import { api } from './api.js';

const MAX_SIDE = { avatar: 640, cover: 1000 };

// Shrink a picture in the browser before uploading: phone photos are often 5–10 MB,
// a cover or an avatar needs ~100–300 KB. Also turns PNG/WEBP into JPEG.
export async function resizeImage(file, maxSide) {
  if (!file.type.startsWith('image/')) throw new Error('Це не схоже на зображення');
  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch {
    throw new Error(
      'Не вдалося відкрити фото. Спробуй JPG або PNG (HEIC з iPhone браузер не читає).',
    );
  }
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close?.();
  return new Promise((resolve, reject) =>
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('Не вдалося підготувати фото'))),
      'image/jpeg',
      0.86,
    ),
  );
}

// Upload one photo straight to S3 (presigned POST from our API).
// kind: 'avatar' | 'cover'. Returns { key, preview } — save `key` in the profile/book.
export async function uploadPhoto(kind, file) {
  const blob = await resizeImage(file, MAX_SIDE[kind]);
  const { key, url, fields } = await api('/uploads', {
    method: 'POST',
    body: JSON.stringify({ kind, content_type: 'image/jpeg' }),
  });
  const form = new FormData();
  Object.entries(fields).forEach(([name, value]) => form.append(name, value));
  form.append('file', blob, 'photo.jpg'); // the file must be the last field
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Не вдалося завантажити фото, спробуй ще раз');
  return { key, preview: URL.createObjectURL(blob) };
}
