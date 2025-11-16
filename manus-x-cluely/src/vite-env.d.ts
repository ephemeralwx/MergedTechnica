/// <reference types="vite/client" />

declare global {
 interface Window {
  electronAPI?: {
   hideWindow: () => void;
   closeWindow: () => void;
   getElevenLabsToken: () => Promise<string>;
   resizeWindow: (width: number, height: number) => void;
  };
 }
}
