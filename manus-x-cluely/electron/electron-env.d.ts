/// <reference types="vite-plugin-electron/electron-env" />

declare namespace NodeJS {
 interface ProcessEnv {
  /**
   * The built directory structure
   *
   * ```tree
   * ├─┬─┬ dist
   * │ │ └── index.html
   * │ │
   * │ ├─┬ dist-electron
   * │ │ ├── main.js
   * │ │ └── preload.js
   * │
   * ```
   */
  APP_ROOT: string;
  /** /dist/ or /public/ */
  VITE_PUBLIC: string;
 }
}

// Used in Renderer process, expose in `preload.ts`
interface Window {
 ipcRenderer: import("electron").IpcRenderer;
 electronAPI: {
  hideWindow: () => void;
  closeWindow: () => void;
  getElevenLabsToken: () => Promise<string>;
  resizeWindow: (width: number, height: number) => void;
  chatCompletion: (
   messages: Array<{ role: string; content: string }>,
  ) => Promise<string>;
  chatStream: (
   messages: Array<{ role: string; content: string }>,
  ) => Promise<string>;
  onChatStreamDelta: (
   callback: (data: { delta: string; fullText: string }) => void,
  ) => void;
  onChatStreamComplete: (
   callback: (data: { fullText: string }) => void,
  ) => void;
  onChatStreamError: (callback: (data: { error: string }) => void) => void;
  removeAllChatStreamListeners: () => void;
 };
}
