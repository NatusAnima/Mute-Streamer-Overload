# TTS Service (lobehub/tts)

This folder contains a minimal Node.js script to generate TTS audio using [lobehub/tts](https://github.com/lobehub/lobe-tts).

## Prerequisites
- Node.js v18 or newer (ESM support required)
- npm (comes with Node.js)

## Setup

1. Open a terminal and navigate to this folder:
   ```sh
   cd tts_service
   ```

2. Install dependencies:
   ```sh
   npm install
   ```

## Usage

Generate an mp3 file from text:

```sh
node generate_tts.mjs "Your text to synthesize goes here."
```

- The output file will be `speech.mp3` in this folder.
- You can change the text as needed.

## Example

```sh
node generate_tts.mjs "Hello, this is a test of the lobehub TTS system."
```

If successful, you will see:
```
TTS audio generated: /path/to/tts_service/speech.mp3
```

## Notes
- You can change the voice or locale in `generate_tts.mjs` if desired (see lobehub/tts docs for options).
- This script is ESM-only and will not work with `require()`. 