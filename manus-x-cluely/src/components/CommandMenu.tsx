import React, { useState, useEffect, useRef } from "react";
import { Command } from "cmdk";
import { Clock, MessageSquare, Search } from "lucide-react";
import "../App.css";
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

interface CommandMenuProps {
 open: boolean;
 onOpenChange: (open: boolean) => void;
 chats: Chat[];
 onSelectChat: (chatId: string) => void;
 onNewChat: () => void;
 onSubmit: (query: string) => void;
}

export function CommandMenu({
 open,
 onOpenChange,
 chats,
 onSelectChat,
 onNewChat,
 onSubmit,
}: CommandMenuProps) {
 const [search, setSearch] = useState("");
 const inputRef = useRef<HTMLInputElement>(null);

 useEffect(() => {
  const down = (e: KeyboardEvent) => {
   if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    onOpenChange(!open);
   }
   if (e.key === "ArrowDown" && !open) {
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement?.classList.contains("prompt-input")) {
     e.preventDefault();
     onOpenChange(true);
    }
   }
  };

  document.addEventListener("keydown", down);
  return () => document.removeEventListener("keydown", down);
 }, [open, onOpenChange]);

 useEffect(() => {
  if (open && inputRef.current) {
   inputRef.current.focus();
  }
 }, [open]);

 const recentChats = chats
  .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
  .slice(0, 10);

 const formatDate = (date: Date) => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) {
   return diffMins === 0 ? "Just now" : `${diffMins}m ago`;
  } else if (diffHours < 24) {
   return `${diffHours}h ago`;
  } else {
   return `${diffDays}d ago`;
  }
 };

 if (!open) return null;

 const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();
  if (search.trim()) {
   onSubmit(search);
   onOpenChange(false);
   setSearch("");
  }
 };

 return (
  <div className="command-menu-inline">
   <Command
    className="command-menu"
    onKeyDown={(e) => {
     if (e.key === "Enter" && search.trim() && !e.defaultPrevented) {
      handleSubmit(e);
     }
    }}
   >
    <div className="command-shine" />
    <form onSubmit={handleSubmit} className="w-full">
     <Command.Input
      ref={inputRef}
      value={search}
      onValueChange={setSearch}
      placeholder="Type a command..."
      className="flex-1 text-lg outline-none w-full prompt-input text-foreground placeholder:text-muted-foreground bg-transparent h-[calc(120px-53px)] px-2!"
     />
    </form>
    <Command.List className="command-list">
     <Command.Empty className="command-empty">No chats found.</Command.Empty>

     <Command.Group heading="Actions" className="command-group">
      <Command.Item
       onSelect={() => {
        onNewChat();
        onOpenChange(false);
       }}
       className="command-item"
      >
       <MessageSquare className="h-4 w-4" />
       <span>New Chat</span>
       <div className="command-meta">⌘N</div>
      </Command.Item>
     </Command.Group>

     {recentChats.length > 0 && (
      <Command.Group heading="Recent Chats" className="command-group">
       {recentChats.map((chat) => (
        <Command.Item
         key={chat.id}
         value={`${chat.title} ${chat.id}`}
         onSelect={() => {
          onSelectChat(chat.id);
          onOpenChange(false);
         }}
         className="command-item"
        >
         <Clock className="h-4 w-4" />
         <div className="flex flex-col flex-1 min-w-0">
          <span className="truncate">{chat.title}</span>
          <span className="text-xs text-muted-foreground truncate">
           {chat.messages.length} message
           {chat.messages.length !== 1 ? "s" : ""}
          </span>
         </div>
         <div className="command-meta">{formatDate(chat.updatedAt)}</div>
        </Command.Item>
       ))}
      </Command.Group>
     )}
    </Command.List>
   </Command>
  </div>
 );
}
