/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AGGREGATOR_WS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
