import { ipcRenderer, contextBridge } from "electron";

// --------- Expose some API to the Renderer process ---------
contextBridge.exposeInMainWorld("ipcRenderer", {
 on(...args: Parameters<typeof ipcRenderer.on>) {
  const [channel, listener] = args;
  return ipcRenderer.on(channel, (event, ...args) => listener(event, ...args));
 },
 off(...args: Parameters<typeof ipcRenderer.off>) {
  const [channel, ...omit] = args;
  return ipcRenderer.off(channel, ...omit);
 },
 send(...args: Parameters<typeof ipcRenderer.send>) {
  const [channel, ...omit] = args;
  return ipcRenderer.send(channel, ...omit);
 },
 invoke(...args: Parameters<typeof ipcRenderer.invoke>) {
  const [channel, ...omit] = args;
  return ipcRenderer.invoke(channel, ...omit);
 },
});

contextBridge.exposeInMainWorld("electronAPI", {
 hideWindow: () => ipcRenderer.send("hide-window"),
 closeWindow: () => ipcRenderer.send("close-window"),
 getElevenLabsToken: () => ipcRenderer.invoke("get-elevenlabs-token"),
 resizeWindow: (width: number, height: number) =>
  ipcRenderer.send("resize-window", width, height),
 chatCompletion: (messages: Array<{ role: string; content: string }>) =>
  ipcRenderer.invoke("chat-completion", messages),
 chatStream: (messages: Array<{ role: string; content: string }>) =>
  ipcRenderer.invoke("chat-stream", messages),
 onChatStreamDelta: (
  callback: (data: { delta: string; fullText: string }) => void,
 ) => ipcRenderer.on("chat-stream-delta", (_, data) => callback(data)),
 onChatStreamComplete: (callback: (data: { fullText: string }) => void) =>
  ipcRenderer.on("chat-stream-complete", (_, data) => callback(data)),
 onChatStreamError: (callback: (data: { error: string }) => void) =>
  ipcRenderer.on("chat-stream-error", (_, data) => callback(data)),
 removeAllChatStreamListeners: () => {
  ipcRenderer.removeAllListeners("chat-stream-delta");
  ipcRenderer.removeAllListeners("chat-stream-complete");
  ipcRenderer.removeAllListeners("chat-stream-error");
 },
 // Agent control methods
 startAgent: (goal: string) => ipcRenderer.invoke("start-agent", goal),
 stopAgent: () => ipcRenderer.invoke("stop-agent"),
 getAgentStatus: () => ipcRenderer.invoke("agent-status"),
 checkAgentServer: () => ipcRenderer.invoke("check-agent-server"),
});