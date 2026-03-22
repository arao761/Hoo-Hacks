import React, { useEffect, useState, ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: ReactNode;
}

export interface ChatItem {
  id: string;
  title: string;
  timestamp: string;
}

export const ChatContext = React.createContext<{
  newChatKey: number;
  chats: ChatItem[];
  addChat: (chat: Omit<ChatItem, 'id'>) => void;
  deleteChat: (id: string) => void;
  onNewChat: () => void;
} | null>(null);

export const Layout = ({ children }: LayoutProps) => {
  const [isMobile, setIsMobile] = useState(false);
  const [newChatKey, setNewChatKey] = useState(0);
  const [chats, setChats] = useState<ChatItem[]>([
    {
      id: "1",
      title: "Spanish Vocabulary Lesson",
      timestamp: "Today",
    },
    {
      id: "2",
      title: "Ancient Egypt Documentary",
      timestamp: "Yesterday",
    },
    {
      id: "3",
      title: "Python Programming Basics",
      timestamp: "2 days ago",
    },
    {
      id: "4",
      title: "Renaissance Art History",
      timestamp: "1 week ago",
    },
    {
      id: "5",
      title: "Marine Biology Deep Dive",
      timestamp: "2 weeks ago",
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
