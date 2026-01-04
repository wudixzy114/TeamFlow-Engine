declare module 'sherpa-onnx-node' {
  export interface FeatConfig {
    sampleRate: number;
    featureDim?: number;
  }

  export interface SenseVoiceConfig {
    model: string;
    tokens: string;
    language?: string;
    useItn?: boolean;
  }

  export interface OfflineModelConfig {
    senseVoice?: SenseVoiceConfig;
    modelType?: string;
    numThreads?: number;
    debug?: number;
    provider?: 'cpu' | 'cuda' | 'coreml';
  }

  export interface OfflineRecognizerConfig {
    featConfig: FeatConfig;
    modelConfig: OfflineModelConfig;
  }

  export interface OfflineStream {
    /**
     * @param sampleRate 采样率 (通常为 16000)
     * @param samples 音频数据 (Float32Array)
     */
    acceptWaveform(sampleRate: number, samples: Float32Array): void;

    getResult(): { text: string };

    free(): void;
  }

  export class OfflineRecognizer {
    constructor(config: OfflineRecognizerConfig);

    createStream(): OfflineStream;

    decode(stream: OfflineStream): void;

    free(): void;
  }
}
