import { EdgeSpeechTTS } from '@lobehub/tts';
import { Buffer } from 'buffer';
import fs from 'fs';
import path from 'path';
import WebSocket from 'ws';

// Polyfill WebSocket for Node.js
global.WebSocket = WebSocket;

async function main() {
  const text = process.argv[2];
  if (!text) {
    console.error('Usage: bun generate_tts.mjs "Your text here"');
    process.exit(1);
  }

  console.log('Initializing TTS...');
  const tts = new EdgeSpeechTTS({ locale: 'en-US' });
  const payload = {
    input: text,
    options: {
      voice: 'es-ES-Ximena:DragonHDLatestNeural',
    },
  };

  try {
    console.log('Sending TTS request...');
    const response = await tts.create(payload);
    console.log('Received response, converting to buffer...');
    const mp3Buffer = Buffer.from(await response.arrayBuffer());
    const speechFile = path.resolve('./speech.mp3');
    fs.writeFileSync(speechFile, mp3Buffer);
    console.log(`TTS audio generated: ${speechFile}`);
  } catch (err) {
    console.error('TTS generation failed:', err);
    process.exit(1);
  }
}

main(); 