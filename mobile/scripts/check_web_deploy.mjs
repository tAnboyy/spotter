// Public Expo variables are baked into the export, so validate before bundling.
const failures = [];
try {
  const url = new URL(process.env.EXPO_PUBLIC_API_URL ?? '');
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      /^(localhost|127\.|0\.0\.0\.0$|\[::1\]$)/i.test(url.hostname)) {
    throw new Error('invalid production URL');
  }
} catch {
  failures.push('Set EXPO_PUBLIC_API_URL to your public HTTPS backend base URL (not localhost).');
}
if (!process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID?.trim()) {
  failures.push('Set EXPO_PUBLIC_GOOGLE_CLIENT_ID to the Google OAuth web client ID used by the backend.');
}
if (failures.length) {
  console.error(`Web deployment configuration is incomplete:\n${failures.join('\n')}`);
  process.exit(1);
}
console.log('Web deployment configuration checked.');
