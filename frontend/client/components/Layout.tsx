import React, { useEffect, useState, ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { useI18n } from "@/i18n";

interface LayoutProps {
  children: ReactNode;
}

export interface ChatItem {
  id: string;
  title?: string;
  titleKey?: string;
  timestamp?: string;
  timestampKey?: string;
}

export const ChatContext = React.createContext<{
  newChatKey: number;
  chats: ChatItem[];
  addChat: (chat: Omit<ChatItem, 'id'>) => void;
  deleteChat: (id: string) => void;
  onNewChat: () => void;
} | null>(null);

export const Layout = ({ children }: LayoutProps) => {
  const { t } = useI18n();
  const [isMobile, setIsMobile] = useState(false);
  const [newChatKey, setNewChatKey] = useState(0);
  const [chats, setChats] = useState<ChatItem[]>([
    {
      id: "1",
      titleKey: "chatHistory.spanishVocabulary",
      timestampKey: "chatHistory.today",
    },
    {
      id: "2",
      titleKey: "chatHistory.ancientEgypt",
      timestampKey: "chatHistory.yesterday",
    },
    {
      id: "3",
      titleKey: "chatHistory.pythonProgramming",
      timestampKey: "chatHistory.twoDaysAgo",
    },
    {
      id: "4",
      titleKey: "chatHistory.renaissanceArt",
      timestampKey: "chatHistory.oneWeekAgo",
    },
    {
      id: "5",
      titleKey: "chatHistory.marineBiology",
      timestampKey: "chatHistory.twoWeeksAgo",
    },
  ]);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleNewChat = () => {
    setNewChatKey((prev) => prev + 1);
  };

  const addChat = (chatData: Omit<ChatItem, 'id'>) => {
    const newChat: ChatItem = {
      id: Date.now().toString(),
      ...chatData,
    };
    setChats((prev) => [newChat, ...prev]);
  };

  const deleteChat = (id: string) => {
    setChats((prev) => prev.filter(chat => chat.id !== id));
  };

  return (
    <ChatContext.Provider value={{ newChatKey, chats, addChat, deleteChat, onNewChat: handleNewChat }}>
      <div className="flex flex-col h-screen bg-gray-50">
        {/* Header */}
        <Header />

        {/* Main content area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <Sidebar isMobile={isMobile} onNewChat={handleNewChat} />

          {/* Page content */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </ChatContext.Provider>
  );
};
