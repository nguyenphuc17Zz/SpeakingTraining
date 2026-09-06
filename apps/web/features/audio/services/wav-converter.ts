/**
 * Memory-safe Audio/PCM WAV Converter using the Web Audio API.
 * Converts recorded browser blobs (e.g., audio/webm, audio/ogg) to standard 16-bit PCM WAV.
 */

export interface WavConversionOptions {
  targetSampleRate?: number;
  numChannels?: number;
}

/**
 * Converts an audio Blob into a 16-bit mono PCM WAV Blob.
 * Ensures the temporary AudioContext is cleanly terminated to avoid memory leaks.
 */
export async function convertToWavBlob(
  blob: Blob,
  options: WavConversionOptions = {}
): Promise<Blob> {
  const targetSampleRate = options.targetSampleRate || 16000;
  const numChannels = options.numChannels || 1;

  const arrayBuffer = await blob.arrayBuffer();
  if (!arrayBuffer.byteLength) {
    throw new Error("Cannot convert empty audio buffer to WAV");
  }

  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  const audioCtx = new AudioCtx();

  try {
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    // Resample to targetSampleRate mono
    const length = Math.floor(audioBuffer.duration * targetSampleRate);
    const offlineCtx = new OfflineAudioContext(numChannels, Math.max(1, length), targetSampleRate);
    const source = offlineCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineCtx.destination);
    source.start();

    const renderedBuffer = await offlineCtx.startRendering();
    const pcmData = renderedBuffer.getChannelData(0);

    // Build 44-byte RIFF WAV header + 16-bit PCM samples
    const wavBuffer = new ArrayBuffer(44 + pcmData.length * 2);
    const view = new DataView(wavBuffer);

    const writeString = (offset: number, str: string) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    };

    writeString(0, "RIFF");
    view.setUint32(4, 36 + pcmData.length * 2, true);
    writeString(8, "WAVE");
    writeString(12, "fmt ");
    view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 = PCM)
    view.setUint16(22, numChannels, true); // NumChannels
    view.setUint32(24, targetSampleRate, true); // SampleRate
    view.setUint32(28, targetSampleRate * numChannels * 2, true); // ByteRate
    view.setUint16(32, numChannels * 2, true); // BlockAlign
    view.setUint16(34, 16, true); // BitsPerSample
    writeString(36, "data");
    view.setUint32(40, pcmData.length * 2, true);

    // Write PCM samples with soft clipping
    let offset = 44;
    for (let i = 0; i < pcmData.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, pcmData[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return new Blob([wavBuffer], { type: "audio/wav" });
  } finally {
    try {
      if (audioCtx.state !== "closed") {
        await audioCtx.close();
      }
    } catch {
      // Ignore close errors on shutdown
    }
  }
}
