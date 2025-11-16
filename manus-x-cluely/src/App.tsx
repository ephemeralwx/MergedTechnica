import { useState, useEffect, useRef, useMemo } from "react";
import "./App.css";
import { Mic, ArrowUp, CornerDownLeft } from "lucide-react";
import { Button } from "./renderer/src/components/ui/button";
import { Toggle } from "./renderer/src/components/ui/toggle";
import { Streamdown } from "streamdown";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupTextarea,
} from "./renderer/src/components/ui/input-group";
import { useScribe } from "@elevenlabs/react";
import { Kbd } from "./renderer/src/components/ui/kbd";
import { CommandMenu } from "./components/CommandMenu";
import { TextShimmer } from "./renderer/src/components/ui/text-shimmer";
import "./components/CommandMenu.css";

type Chat = {
  id: string;
  title: string;
  messages: Array<{
    id: string;
    text: string;
    timestamp: Date;
    role: "user" | "assistant";
  }>;
  createdAt: Date;
  updatedAt: Date;
};

function App() {
  const [query, setQuery] = useState("");
  const [baseQuery, setBaseQuery] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isChatRecording, setIsChatRecording] = useState(false);
  const [chatBaseMessage, setChatBaseMessage] = useState("");
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [commandMenuOpen, setCommandMenuOpen] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );

  // Agent state
  const [agentEnabled, setAgentEnabled] = useState(false);
  const [agentRunning, setAgentRunning] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const chatSilenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const currentChat = chats.find((chat) => chat.id === currentChatId);
  const chatMessages = useMemo(
    () => currentChat?.messages || [],
    [currentChat?.messages]
  );

  const stopRecording = () => {
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    setIsRecording(false);
  };

  const scribe = useScribe({
    modelId: "scribe_v2_realtime",
    onPartialTranscript: (data) => {
      console.log("Partial:", data.text);

      if (isChatRecording) {
        const currentText = chatBaseMessage.trim();
        const preview = currentText ? currentText + " " + data.text : data.text;
        setNewMessage(preview);

        if (chatSilenceTimeoutRef.current) {
          clearTimeout(chatSilenceTimeoutRef.current);
        }

        chatSilenceTimeoutRef.current = setTimeout(() => {
          if (isChatRecording && scribe.isConnected) {
            console.log(
              "Auto-stopping chat recording after 3 seconds of silence"
            );
            scribe.disconnect();
            setIsChatRecording(false);
          }
        }, 3000);
      } else {
        const currentText = baseQuery.trim();
        const preview = currentText ? currentText + " " + data.text : data.text;
        setQuery(preview);

        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }

        silenceTimeoutRef.current = setTimeout(() => {
          if (isRecording && scribe.isConnected) {
            console.log("Auto-stopping after 3 seconds of silence");
            scribe.disconnect();
            stopRecording();
          }
        }, 3000);
      }
    },
    onCommittedTranscript: (data) => {
      console.log("Committed:", data.text);
      const newText = data.text.trim();
      if (newText) {
        if (isChatRecording) {
          const currentText = chatBaseMessage.trim();
          const finalText = currentText ? currentText + " " + newText : newText;
          setNewMessage(finalText);
          setChatBaseMessage(finalText);
        } else {
          const currentText = baseQuery.trim();
          const finalText = currentText ? currentText + " " + newText : newText;
          setQuery(finalText);
          setBaseQuery(finalText);
          if (inputRef.current) {
            inputRef.current.focus();
          }
        }
      }

      if (isChatRecording && chatSilenceTimeoutRef.current) {
        clearTimeout(chatSilenceTimeoutRef.current);
        chatSilenceTimeoutRef.current = null;
      } else if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
    },
  });

  useEffect(() => {
    const savedChats = localStorage.getItem("ai-chat-history");
    if (savedChats) {
      try {
        const parsedChats = JSON.parse(savedChats).map(
          (chat: {
            id: string;
            title: string;
            messages: Array<{
              id: string;
              text: string;
              timestamp: string;
              role: string;
            }>;
            createdAt: string;
            updatedAt: string;
          }) => ({
            ...chat,
            createdAt: new Date(chat.createdAt),
            updatedAt: new Date(chat.updatedAt),
            messages: chat.messages.map(
              (msg: {
                id: string;
                text: string;
                timestamp: string;
                role: string;
              }) => ({
                ...msg,
                timestamp: new Date(msg.timestamp),
              })
            ),
          })
        );
        setChats(parsedChats);
      } catch (error) {
        console.error("Failed to load chat history:", error);
      }
    }
  }, []);

  useEffect(() => {
    if (chats.length > 0) {
      localStorage.setItem("ai-chat-history", JSON.stringify(chats));
    }
  }, [chats]);

  useEffect(() => {
    if (!window.electronAPI) return;

    const handleStreamDelta = (data: { delta: string; fullText: string }) => {
      if (streamingMessageId) {
        setChats((prevChats) =>
          prevChats.map((chat) => ({
            ...chat,
            messages: chat.messages.map((msg) =>
              msg.id === streamingMessageId
                ? { ...msg, text: data.fullText }
                : msg
            ),
          }))
        );
      }
    };

    const handleStreamComplete = () => {
      setIsLoading(false);
      setStreamingMessageId(null);
    };

    const handleStreamError = (data: { error: string }) => {
      console.error("Stream error:", data.error);
      setIsLoading(false);
      setStreamingMessageId(null);
    };

    window.electronAPI.onChatStreamDelta(handleStreamDelta);
    window.electronAPI.onChatStreamComplete(handleStreamComplete);
    window.electronAPI.onChatStreamError(handleStreamError);

    return () => {
      window.electronAPI.removeAllChatStreamListeners();
    };
  }, [streamingMessageId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (commandMenuOpen) {
          setCommandMenuOpen(false);
          if (window.electronAPI) {
            window.electronAPI.resizeWindow(600, 120);
          }
        } else if (showChat) {
          setShowChat(false);
          if (window.electronAPI) {
            window.electronAPI.resizeWindow(600, 120);
          }
        } else {
          setQuery("");
          if (window.electronAPI) {
            // window.electronAPI.hideWindow();
          }
        }
      }
      if (e.key === "n" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        createNewChatFromMain();
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (
        commandMenuOpen &&
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setCommandMenuOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showChat, commandMenuOpen]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    return () => {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      if (chatSilenceTimeoutRef.current) {
        clearTimeout(chatSilenceTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages, isLoading]);

  const createNewChat = (firstMessage: string): Chat => {
    const chatId = Date.now().toString();
    return {
      id: chatId,
      title:
        firstMessage.slice(0, 50) + (firstMessage.length > 50 ? "..." : ""),
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  };

  const addMessageToChat = (
    chatId: string,
    message: {
      id: string;
      text: string;
      timestamp: Date;
      role: "user" | "assistant";
    }
  ) => {
    setChats((prevChats) =>
      prevChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              messages: [...chat.messages, message],
              updatedAt: new Date(),
            }
          : chat
      )
    );
  };

  const handleAgentToggle = async (pressed: boolean) => {
    setAgentEnabled(pressed);

    if (!pressed && agentRunning) {
      // Stop the agent if it's running when toggled off
      try {
        await window.electronAPI.stopAgent();
        setAgentRunning(false);
      } catch (error) {
        console.error("Failed to stop agent:", error);
      }
    }
  };

  const handleSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    e?.preventDefault();
    const queryToUse = customQuery || query;
    if (queryToUse.trim() && !isLoading) {
      const userMessage = queryToUse.trim();
      if (!customQuery) setQuery("");
      setIsLoading(true);

      let chatId = currentChatId;
      if (!chatId) {
        const newChat = createNewChat(userMessage);
        setChats((prev) => [newChat, ...prev]);
        chatId = newChat.id;
        setCurrentChatId(chatId);
      }

      setShowChat(true);
      if (window.electronAPI) {
        window.electronAPI.resizeWindow(600, 400);
      }

      const userMessageObj = {
        id: Date.now().toString(),
        text: userMessage,
        timestamp: new Date(),
        role: "user" as const,
      };

      addMessageToChat(chatId, userMessageObj);

      try {
        const currentChatMessages =
          chats.find((chat) => chat.id === chatId)?.messages || [];
        const messages = [...currentChatMessages, userMessageObj].map(
          (msg) => ({
            role: msg.role,
            content: msg.text,
          })
        );

        const assistantMessageId = (Date.now() + 1).toString();
        const assistantMessage = {
          id: assistantMessageId,
          text: "",
          timestamp: new Date(),
          role: "assistant" as const,
        };

        addMessageToChat(chatId, assistantMessage);
        setStreamingMessageId(assistantMessageId);

        await window.electronAPI.chatStream(messages);
      } catch (error) {
        console.error("Error getting AI response:", error);
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          text: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
          role: "assistant" as const,
        };
        addMessageToChat(chatId, errorMessage);
        setIsLoading(false);
        setStreamingMessageId(null);
      }
    }
  };

  const handleNewMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      text: newMessage.trim(),
      timestamp: new Date(),
      role: "user" as const,
    };

    // ===== AGENT MODE HANDLING =====
    if (agentEnabled) {
      try {
        setAgentRunning(true);

        // Ensure we have a chat to add messages to
        let chatId = currentChatId;
        if (!chatId) {
          const newChat = createNewChat(newMessage.trim());
          setChats((prev) => [newChat, ...prev]);
          chatId = newChat.id;
          setCurrentChatId(chatId);
        }

        // Add user message to chat
        addMessageToChat(chatId, userMessage);

        // Start the agent
        const response = await window.electronAPI.startAgent(newMessage.trim());

        // Add agent status message
        const agentMessage = {
          id: (Date.now() + 1).toString(),
          text: `🤖 Agent started with goal: "${newMessage.trim()}"\n\nThe agent is now executing your command autonomously. Check the terminal for detailed progress.`,
          timestamp: new Date(),
          role: "assistant" as const,
        };

        addMessageToChat(chatId, agentMessage);
        setNewMessage("");

        // Poll for agent completion
        const pollInterval = setInterval(async () => {
          try {
            const status = await window.electronAPI.getAgentStatus();
            if (!status.running) {
              clearInterval(pollInterval);
              setAgentRunning(false);

              // Add completion message
              const completionMessage = {
                id: Date.now().toString(),
                text: status.error
                  ? `❌ Agent encountered an error: ${status.error}`
                  : `✅ Agent completed the goal: "${status.goal}"`,
                timestamp: new Date(),
                role: "assistant" as const,
              };

              addMessageToChat(chatId, completionMessage);
            }
          } catch (error) {
            clearInterval(pollInterval);
            setAgentRunning(false);
          }
        }, 2000);
      } catch (error) {
        console.error("Agent error:", error);
        setAgentRunning(false);

        const errorMessage = {
          id: (Date.now() + 1).toString(),
          text: `❌ Failed to start agent: ${
            (error as Error).message
          }\n\nMake sure the agent server is running on http://127.0.0.1:5001`,
          timestamp: new Date(),
          role: "assistant" as const,
        };

        let chatId = currentChatId;
        if (!chatId) {
          const newChat = createNewChat(newMessage.trim());
          setChats((prev) => [newChat, ...prev]);
          chatId = newChat.id;
          setCurrentChatId(chatId);
        }

        addMessageToChat(chatId, userMessage);
        addMessageToChat(chatId, errorMessage);
      }
      return;
    }

    // ===== ORIGINAL CHAT MODE HANDLING =====
    if (currentChatId) {
      setNewMessage("");
      setIsLoading(true);

      addMessageToChat(currentChatId, userMessage);

      try {
        const currentChatMessages =
          chats.find((chat) => chat.id === currentChatId)?.messages || [];
        const messages = [...currentChatMessages, userMessage].map((msg) => ({
          role: msg.role,
          content: msg.text,
        }));

        const assistantMessageId = (Date.now() + 1).toString();
        const assistantMessage = {
          id: assistantMessageId,
          text: "",
          timestamp: new Date(),
          role: "assistant" as const,
        };

        addMessageToChat(currentChatId, assistantMessage);
        setStreamingMessageId(assistantMessageId);

        await window.electronAPI.chatStream(messages);
      } catch (error) {
        console.error("Error getting AI response:", error);
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          text: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
          role: "assistant" as const,
        };
        addMessageToChat(currentChatId, errorMessage);
        setIsLoading(false);
        setStreamingMessageId(null);
      }
    }
  };

  const handleChatMicClick = async () => {
    if (isChatRecording) {
      try {
        if (scribe.isConnected) {
          scribe.disconnect();
        }
        if (chatSilenceTimeoutRef.current) {
          clearTimeout(chatSilenceTimeoutRef.current);
          chatSilenceTimeoutRef.current = null;
        }
        setIsChatRecording(false);
      } catch (error) {
        console.error("Error stopping chat recording:", error);
        setIsChatRecording(false);
      }
    } else {
      try {
        // Disconnect any existing connection first
        if (scribe.isConnected) {
          scribe.disconnect();
          // Stop main recording if it's active
          if (isRecording) {
            setIsRecording(false);
            if (silenceTimeoutRef.current) {
              clearTimeout(silenceTimeoutRef.current);
              silenceTimeoutRef.current = null;
            }
          }
          // Wait a moment for the disconnect to complete
          await new Promise((resolve) => setTimeout(resolve, 120));
        }

        const token = await fetchTokenFromServer();
        setChatBaseMessage(newMessage);
        await scribe.connect({
          token,
          microphone: {
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
        setIsChatRecording(true);
      } catch (error) {
        console.error("Error connecting to scribe for chat:", error);
        setIsChatRecording(false);
        alert(
          `Error connecting to speech recognition: ${(error as Error).message}`
        );
      }
    }
  };

  const fetchTokenFromServer = async (): Promise<string> => {
    try {
      console.log("Checking for electronAPI...", !!window.electronAPI);
      if (window.electronAPI?.getElevenLabsToken) {
        console.log("Calling getElevenLabsToken...");
        const token = await window.electronAPI.getElevenLabsToken();
        console.log("Token received:", token ? "✓" : "✗");
        return token;
      } else {
        throw new Error("Electron API not available");
      }
    } catch (error) {
      console.error("Error fetching token:", error);
      throw error;
    }
  };

  const handleMicClick = async () => {
    console.log("Mic button clicked, isRecording:", isRecording);

    if (isRecording) {
      console.log("Stopping recording...");
      try {
        if (scribe.isConnected) {
          scribe.disconnect();
        }
        stopRecording();
        console.log("Successfully stopped recording");
      } catch (error) {
        console.error("Error stopping recording:", error);
        stopRecording();
      }
    } else {
      try {
        // Disconnect any existing connection first
        if (scribe.isConnected) {
          scribe.disconnect();
          // Stop chat recording if it's active
          if (isChatRecording) {
            setIsChatRecording(false);
            if (chatSilenceTimeoutRef.current) {
              clearTimeout(chatSilenceTimeoutRef.current);
              chatSilenceTimeoutRef.current = null;
            }
          }
          // Wait a moment for the disconnect to complete
          await new Promise((resolve) => setTimeout(resolve, 120));
        }

        console.log("Fetching token...");
        const token = await fetchTokenFromServer();
        console.log("Token received, connecting to scribe...");

        setBaseQuery(query);
        await scribe.connect({
          token,
          microphone: {
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
        setIsRecording(true);
        console.log("Connected to scribe successfully");
      } catch (error) {
        console.error("Error connecting to scribe:", error);
        setIsRecording(false);
        alert(
          `Error connecting to speech recognition: ${(error as Error).message}`
        );
      }
    }
  };

  const createNewChatFromMain = () => {
    setCurrentChatId(null);
    setShowChat(false);
    setCommandMenuOpen(false);
    if (window.electronAPI) {
      window.electronAPI.resizeWindow(600, 120);
    }
  };

  const selectChat = (chatId: string) => {
    setCurrentChatId(chatId);
    setShowChat(true);
    setCommandMenuOpen(false);
    if (window.electronAPI) {
      window.electronAPI.resizeWindow(600, 500);
    }
  };

  return (
    <div className="flex w-full origin-top flex-col items-between justify-center overflow-hidden border-border border bg-stone-900/90 rounded-xl h-full transition-all duration-200 ease-out relative">
      {showChat ? (
        <div className="w-full h-full flex flex-col px-4">
          <div className="flex justify-between items-center border-b border-border pt-4 pb-2 fixed top-0 w-[calc(100%-(var(--spacing)*8))] bg-stone-900 mt-px">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium">
                {currentChat?.title || "AI Chat"}
              </h3>
            </div>
            <div className="flex items-center gap-1">
              {/*<Button
        size="sm"
        variant="ghost"
        onClick={createNewChatFromMain}
        className="px-2 h-8 text-xs"
        title="New Chat"
       >
        <Plus className="h-3 w-3" />
       </Button>*/}
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setShowChat(false);
                  if (window.electronAPI) {
                    window.electronAPI.resizeWindow(600, 120);
                  }
                }}
                className="px-2 h-8 text-xs bg-stone-800"
              >
                <Kbd className="bg-white/10">esc</Kbd>
                Back
              </Button>
            </div>
          </div>
          <div
            className="flex-1 overflow-y-auto pt-4 pb-20"
            ref={chatContainerRef}
          >
            {chatMessages.length === 0 ? (
              <div className="text-muted-foreground text-sm text-center py-8">
                <div className="mb-2">👋 Hi! I'm your AI assistant.</div>
                <div>Ask me anything to get started.</div>
              </div>
            ) : (
              <div className="space-y-3">
                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex flex-col gap-1 px-4 ${
                      message.role === "user" ? "first:pt-16" : ""
                    }`}
                  >
                    <div
                      className={`flex items-center  ${
                        message.role === "user"
                          ? "justify-end"
                          : "justify-start"
                      }`}
                    >
                      <span className="text-xs text-muted-foreground">
                        {message.role === "user" ? "You" : "AI"}
                      </span>
                    </div>
                    <div
                      className={`text-sm  text-foreground ${
                        message.role === "user" ? "ml-auto" : ""
                      }`}
                    >
                      {message.role === "assistant" ? (
                        <Streamdown
                          isAnimating={streamingMessageId === message.id}
                          className="prose prose-sm prose-invert max-w-none"
                        >
                          {message.text}
                        </Streamdown>
                      ) : (
                        message.text
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex flex-col gap-1 px-4">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-muted-foreground">AI</span>
                    </div>
                    <TextShimmer duration={3}>Loading</TextShimmer>
                  </div>
                )}
              </div>
            )}
          </div>
          <form onSubmit={handleNewMessage} className="pb-4 ">
            <InputGroup className="bg-stone-800">
              <InputGroupTextarea
                size={"sm"}
                value={newMessage}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setNewMessage(e.target.value)
                }
                placeholder="Type a message..."
                className="placeholder:text-muted-foreground! text-sm"
                onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (newMessage.trim()) {
                      handleNewMessage(e);
                    }
                  }
                }}
              />
              <InputGroupAddon align="block-end" className="justify-between ">
                <Toggle
                  className={"text-xs"}
                  pressed={agentEnabled}
                  onPressedChange={handleAgentToggle}
                >
                  Agent {agentRunning && "🟢"}
                </Toggle>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    size="icon-xs"
                    variant={isChatRecording ? "destructive" : "ghost"}
                    className="rounded-full"
                    disabled={isLoading}
                    onClick={handleChatMicClick}
                  >
                    {/*{isChatRecording ? (*/}
                    {/*<MicOff className="h-4 w-4" strokeWidth={2.25} />*/}
                    {/*) : (*/}
                    <Mic className="h-4 w-4" strokeWidth={2.25} />
                    {/*)}*/}
                  </Button>
                  <Button
                    type="submit"
                    size="icon-xs"
                    className="rounded-full"
                    disabled={!newMessage.trim() || isLoading}
                  >
                    <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
                  </Button>
                </div>
              </InputGroupAddon>
            </InputGroup>
          </form>
        </div>
      ) : (
        <>
          {commandMenuOpen ? (
            <>
              <div className="w-full flex-1 flex items-start px-2 scroll-py-2 overflow-scrollx ">
                <CommandMenu
                  open={commandMenuOpen}
                  onOpenChange={setCommandMenuOpen}
                  chats={chats}
                  onSelectChat={selectChat}
                  onNewChat={createNewChatFromMain}
                  onSubmit={(query: string) => handleSubmit(undefined, query)}
                />
                {/*<Button
         size="icon"
         variant={isRecording ? "destructive" : "outline"}
         className=" mx-0"
         onClick={handleMicClick}
         type="button"
        >
         <Mic />
        </Button>*/}
              </div>
              <div className="bg-background/80 h-fit w-full px-4 py-4 flex items-center gap-2 justify-end border-t absolute bottom-0">
                <p className="text-sm text-muted-foreground">
                  Press Enter to send
                </p>
                <Kbd>
                  <CornerDownLeft />
                </Kbd>
              </div>
            </>
          ) : (
            <>
              <div className="relative w-full h-full">
                <form
                  onSubmit={handleSubmit}
                  className={`w-full box-border transition-all duration-300 h-full flex items-center px-4 py-3`}
                >
                  <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      if (!scribe.isConnected) {
                        setBaseQuery(e.target.value);
                      }
                    }}
                    placeholder="Type a command..."
                    autoComplete="off"
                    className="flex-1 text-lg outline-none w-full prompt-input text-foreground placeholder:text-muted-foreground bg-transparent"
                    spellCheck="false"
                    onKeyDown={(e) => {
                      if (e.key === "ArrowDown") {
                        e.preventDefault();
                        setCommandMenuOpen(true);
                        if (window.electronAPI) {
                          window.electronAPI.resizeWindow(600, 500);
                        }
                      }
                    }}
                  />
                  <Button
                    size="icon"
                    variant={isRecording ? "destructive" : "outline"}
                    className=" mx-0"
                    onClick={handleMicClick}
                    type="button"
                  >
                    {/*{isRecording ? <MicOff /> : <Mic />}*/}
                    <Mic />
                  </Button>
                </form>
              </div>
              <div className="bg-background/80 h-fit w-full px-4 py-4 flex items-center gap-2 justify-end border-t">
                <p className="text-sm text-muted-foreground">
                  Press Enter to send
                </p>
                <Kbd>
                  <CornerDownLeft />
                </Kbd>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;
