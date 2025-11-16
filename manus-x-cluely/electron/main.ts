import { app, BrowserWindow, globalShortcut, ipcMain } from "electron";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fetch from "node-fetch";
import dotenv from "dotenv";
import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load environment variables from the project root
dotenv.config({ path: path.join(__dirname, "..", ".env.local") });
dotenv.config({ path: path.join(__dirname, "..", ".env") });

console.log("Environment variables loaded:");
console.log("Project root:", path.join(__dirname, ".."));
console.log("Has ELEVENLABS_API_KEY:", !!process.env.ELEVENLABS_API_KEY);
console.log("Has OPENAI_API_KEY:", !!process.env.OPENAI_API_KEY);

process.env.APP_ROOT = path.join(__dirname, "..");

export const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
export const MAIN_DIST = path.join(process.env.APP_ROOT, "dist-electron");
export const RENDERER_DIST = path.join(process.env.APP_ROOT, "dist");

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL
 ? path.join(process.env.APP_ROOT, "public")
 : RENDERER_DIST;

let win: BrowserWindow | null;

function createWindow() {
 win = new BrowserWindow({
  width: 600,
  height: 120,
  frame: false,
  // titleBarStyle: "hidden",
  // resizable: true,
  transparent: true,
  alwaysOnTop: true,
  skipTaskbar: true,
  // show: false,
  // vibrancy: "hud",
  roundedCorners: false,
  // hasShadow: false,
  // visualEffectState: "active",
  webPreferences: {
   preload: path.join(__dirname, "preload.mjs"),
   nodeIntegration: false,
   contextIsolation: true,
  },
 });

 win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

 win.on("blur", () => {
  if (win && win.isVisible()) {
   win.hide();
  }
 });

 if (VITE_DEV_SERVER_URL) {
  win.loadURL(VITE_DEV_SERVER_URL);
 } else {
  win.loadFile(path.join(RENDERER_DIST, "index.html"));
 }
}

function centerWindow() {
 if (!win) return;

 const { screen } = require("electron");
 const primaryDisplay = screen.getPrimaryDisplay();
 const { width, height } = primaryDisplay.workAreaSize;

 const windowBounds = win.getBounds();
 const x = Math.round((width - windowBounds.width) / 2);
 const y = Math.round(height / 4);

 win.setPosition(x, y);
}

function toggleWindow() {
 if (!win) return;

 if (win.isVisible()) {
  win.hide();
 } else {
  centerWindow();
  win.show();
  win.focus();
 }
}

app.whenReady().then(() => {
 createWindow();

 globalShortcut.register("CommandOrControl+Space", () => {
  toggleWindow();
 });

 ipcMain.on("hide-window", () => {
  if (win) {
   win.hide();
  }
 });

 ipcMain.on("close-window", () => {
  if (win) {
   win.close();
  }
 });

 ipcMain.on("resize-window", (event, width, height) => {
  if (win) {
   win.setSize(width, height);
   centerWindow();
  }
 });

 ipcMain.handle("get-elevenlabs-token", async () => {
  try {
   const apiKey = process.env.ELEVENLABS_API_KEY;
   console.log("API Key exists:", !!apiKey);
   console.log("API Key length:", apiKey?.length || 0);

   if (!apiKey) {
    throw new Error("ELEVENLABS_API_KEY environment variable is not set");
   }

   const response = await fetch(
    "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe",
    {
     method: "POST",
     headers: {
      "xi-api-key": apiKey,
     },
    },
   );

   console.log("Token response status:", response.status);

   if (!response.ok) {
    const errorText = await response.text();
    console.error("Token fetch error:", errorText);
    throw new Error(
     `Failed to fetch token: ${response.statusText} - ${errorText}`,
    );
   }

   const data = await response.json();
   console.log("Token generated successfully");
   return data.token;
  } catch (error) {
   console.error("Error generating ElevenLabs token:", error);
   throw error;
  }
 });

 ipcMain.handle("chat-completion", async (event, messages) => {
  try {
   const apiKey = process.env.OPENAI_API_KEY;

   if (!apiKey) {
    throw new Error("OPENAI_API_KEY environment variable is not set");
   }

   const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
     Authorization: `Bearer ${apiKey}`,
     "Content-Type": "application/json",
    },
    body: JSON.stringify({
     model: "gpt-4o-mini",
     messages: messages,
     temperature: 0.7,
     max_tokens: 1000,
    }),
   });

   if (!response.ok) {
    const errorText = await response.text();
    console.error("OpenAI API error:", errorText);
    throw new Error(`OpenAI API error: ${response.statusText}`);
   }

   const data = await response.json();
   return data.choices[0].message.content;
  } catch (error) {
   console.error("Error in chat completion:", error);
   throw error;
  }
 });

 ipcMain.handle("chat-stream", async (event, messages) => {
  try {
   const apiKey = process.env.OPENAI_API_KEY;

   if (!apiKey) {
    throw new Error("OPENAI_API_KEY environment variable is not set");
   }

   const result = await streamText({
    model: openai("gpt-4o-mini", {
     apiKey: apiKey,
    }),
    messages: messages,
    temperature: 0.7,
    maxTokens: 1000,
   });

   let fullResponse = "";

   for await (const delta of result.textStream) {
    fullResponse += delta;
    // Send partial response to renderer
    event.sender.send("chat-stream-delta", {
     delta: delta,
     fullText: fullResponse,
    });
   }

   // Send final response
   event.sender.send("chat-stream-complete", {
    fullText: fullResponse,
   });

   return fullResponse;
  } catch (error) {
   console.error("Error in chat stream:", error);
   event.sender.send("chat-stream-error", { error: error.message });
   throw error;
  }
 });

 // ============================================================================
 // AGENT CONTROL ENDPOINTS
 // ============================================================================

 ipcMain.handle("start-agent", async (event, goal) => {
  try {
   console.log(`Starting agent with goal: ${goal}`);
   
   const response = await fetch("http://127.0.0.1:5001/agent/start", {
    method: "POST",
    headers: {
     "Content-Type": "application/json",
    },
    body: JSON.stringify({ goal }),
   });

   if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || "Failed to start agent");
   }

   const data = await response.json();
   return data;
  } catch (error) {
   console.error("Error starting agent:", error);
   throw error;
  }
 });

 ipcMain.handle("stop-agent", async () => {
  try {
   console.log("Stopping agent...");
   
   const response = await fetch("http://127.0.0.1:5001/agent/stop", {
    method: "POST",
   });

   if (!response.ok) {
    throw new Error("Failed to stop agent");
   }

   const data = await response.json();
   return data;
  } catch (error) {
   console.error("Error stopping agent:", error);
   throw error;
  }
 });

 ipcMain.handle("agent-status", async () => {
  try {
   const response = await fetch("http://127.0.0.1:5001/agent/status");
   
   if (!response.ok) {
    throw new Error("Failed to get agent status");
   }

   const data = await response.json();
   return data;
  } catch (error) {
   console.error("Error getting agent status:", error);
   return { running: false, error: error.message };
  }
 });

 ipcMain.handle("check-agent-server", async () => {
  try {
   const response = await fetch("http://127.0.0.1:5001/health");
   
   if (!response.ok) {
    return { healthy: false };
   }

   const data = await response.json();
   return data;
  } catch (error) {
   return { healthy: false, error: error.message };
  }
 });
});

app.on("window-all-closed", () => {
 if (process.platform !== "darwin") {
  app.quit();
  win = null;
 }
});

app.on("activate", () => {
 if (BrowserWindow.getAllWindows().length === 0) {
  createWindow();
 }
});

app.on("will-quit", () => {
 globalShortcut.unregisterAll();
});