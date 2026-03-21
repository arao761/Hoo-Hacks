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
  onNewChat: () => void;
} | null>(null);

export const Layout = ({ children }: LayoutProps) => {
  const [isMobile, setIsMobile] = useState(false);
  const [newChatKey, setNewChatKey] = useState(0);

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

  return (
    <ChatContext.Provider value={{ newChatKey, onNewChat: handleNewChat }}>
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
