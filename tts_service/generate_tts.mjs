import { EdgeSpeechTTS } from '@lobehub/tts';
import { Buffer } from 'buffer';
import fs from 'fs';
import path from 'path';
import WebSocket from 'ws';
import { execSync } from 'child_process';

// Polyfill WebSocket for Node.js
global.WebSocket = WebSocket;

function parseArgs() {
  const args = process.argv.slice(2);
  let text = null;
  let voice = 'en-GB-SoniaNeural';
  let volume = 1.0;
  let i = 0;
  let pitch = 1.0;
  let speed = 1.0;
  while (i < args.length) {
    if (!text) {
      text = args[i++];
      continue;
    }
    const arg = args[i++];
    if (arg === '--voice') voice = args[i++];
    else if (arg === '--volume') volume = parseFloat(args[i++]);
    else if (arg === '--pitch') pitch = parseFloat(args[i++]);
    else if (arg === '--speed') speed = parseFloat(args[i++]);
  }
  return { text, voice, volume, pitch, speed };
}

async function main() {
  const { text, voice, volume, pitch, speed } = parseArgs();
  if (!text) {
    console.error('Usage: bun generate_tts.mjs "Your text here" --voice <voice> --volume <volume> --pitch <pitch> --speed <speed>');
    process.exit(1);
  }

  console.log('Initializing TTS...');
  const tts = new EdgeSpeechTTS({ locale: 'en-US' });

  const payload = {
    input: text,
    options: {
      voice: voice,
    },
  };

  console.log('TTS payload:', JSON.stringify(payload, null, 2));

  try {
    console.log('Sending TTS request...');
    const response = await tts.create(payload);
    console.log('Received response, converting to buffer...');
    const mp3Buffer = Buffer.from(await response.arrayBuffer());
    const rawDir = decodeURIComponent(new URL(import.meta.url).pathname);
    let __dirname = path.dirname(rawDir);
    if (process.platform === 'win32' && __dirname.startsWith('/')) {
      __dirname = __dirname.slice(1);
    }
    const speechFile = path.join(__dirname, 'speech.mp3');
    fs.mkdirSync(__dirname, { recursive: true }); // Ensure directory exists
    fs.writeFileSync(speechFile, mp3Buffer);

    // Amplify the MP3 by volume factor (default 1.0 = no change)
    if (volume !== 1.0) {
      try {
        execSync(`ffmpeg -y -i "${speechFile}" -filter:a "volume=${volume}" -ar 44100 -ac 2 -b:a 192k "${speechFile}.loud.mp3"`);
        fs.renameSync(`${speechFile}.loud.mp3`, speechFile);
        console.log('Amplified TTS audio.');
      } catch (e) {
        console.error('Failed to amplify audio (is ffmpeg installed and in PATH?):', e);
      }
    }

    // Apply pitch shift if needed (default 1.0 = no change)
    // Use rubberband: --pitch 1.01 = +1% pitch, 0.99 = -1% pitch
    if (Math.abs(pitch - 1.0) > 0.0001) {
      try {
        const roundedPitch = Number(pitch.toFixed(4));
        execSync(`ffmpeg -y -i "${speechFile}" -filter:a "rubberband=pitch=${roundedPitch}" -ar 44100 -ac 2 -b:a 192k "${speechFile}.pitch.mp3"`);
        fs.renameSync(`${speechFile}.pitch.mp3`, speechFile);
        console.log(`Applied pitch shift: ${roundedPitch}x (rubberband)`);
      } catch (e) {
        console.error('Failed to change pitch (is ffmpeg with rubberband installed and in PATH?):', e);
      }
    }

    // Apply speed/rate change if needed (default 1.0 = no change)
    if (speed !== 1.0) {
      try {
        // FFmpeg atempo supports 0.5-2.0 per filter, chain if outside
        let atempoFilters = [];
        let s = speed;
        while (s > 2.0) { atempoFilters.push('atempo=2.0'); s /= 2.0; }
        while (s < 0.5) { atempoFilters.push('atempo=0.5'); s /= 0.5; }
        atempoFilters.push(`atempo=${s}`);
        const atempoStr = atempoFilters.join(',');
        execSync(`ffmpeg -y -i "${speechFile}" -filter:a "${atempoStr}" -ar 44100 -ac 2 -b:a 192k "${speechFile}.speed.mp3"`);
        fs.renameSync(`${speechFile}.speed.mp3`, speechFile);
        console.log('Applied speed/rate change to TTS audio.');
      } catch (e) {
        console.error('Failed to change speed/rate (is ffmpeg installed and in PATH?):', e);
      }
    }
    console.log(`TTS audio generated: ${speechFile}`);
  } catch (err) {
    console.error('TTS generation failed:', err);
    if (err && err.stack) {
      console.error(err.stack);
    }
    process.exit(1);
  }
}

main(); 