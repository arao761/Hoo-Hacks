import { useState, useContext, useMemo } from "react";
import { Menu, X, Plus, Search, MessageCircle, Trash2 } from "lucide-react";
import { ChatContext, ChatItem } from "./Layout";
import { useI18n } from "@/i18n";

interface SidebarProps {
  isMobile?: boolean;
  onNewChat: () => void;
}

export const Sidebar = ({ isMobile = false, onNewChat }: SidebarProps) => {
  const [isOpen, setIsOpen] = useState(!isMobile);
  const [searchQuery, setSearchQuery] = useState("");
  const chatContext = useContext(ChatContext);

  const { t } = useI18n();
  const chats = chatContext?.chats || [];
  const addChat = chatContext?.addChat;
  const deleteChat = chatContext?.deleteChat;

  const localize = (chat: ChatItem) => ({
    title: chat.titleKey ? t(chat.titleKey) : chat.title || "",
    timestamp: chat.timestampKey ? t(chat.timestampKey) : chat.timestamp || "",
  });

  // Filter and sort chats based on search query
  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) {
      return chats;
    }

    const query = searchQuery.toLowerCase();
    const matching = [];
    const nonMatching = [];

    for (const chat of chats) {
      const localized = localize(chat);
      if (localized.title.toLowerCase().includes(query)) {
        matching.push(chat);
      } else {
        nonMatching.push(chat);
      }
    }

    return [...matching, ...nonMatching];
  }, [chats, searchQuery]);

  const handleNewChat = () => {
    onNewChat();
    setSearchQuery(""); // Clear search when starting new chat
  };

  const handleDeleteChat = (chatId: string) => {
    if (deleteChat) {
      deleteChat(chatId);
    }
  };

  const handleChatClick = (chat: ChatItem) => {
    // TODO: Implement chat loading functionality
    console.log("Clicked chat:", chat.title);
    // For now, just clear search and close mobile sidebar
    setSearchQuery("");
    if (isMobile) {
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* Mobile menu button */}
      {isMobile && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="fixed top-20 left-4 z-40 p-2 bg-hooslearn-orange text-white rounded-lg hover:bg-hooslearn-orange-dark transition-all"
        >
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      )}

      {/* Sidebar overlay for mobile */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 top-20"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          ${
            isMobile
              ? `fixed top-20 left-0 h-[calc(100vh-80px)] w-64 z-30 transform transition-transform duration-300 ${
                  isOpen ? "translate-x-0" : "-translate-x-full"
                }`
              : "relative w-64 h-[calc(100vh-80px)]"
          }
          bg-white border-r-2 border-hooslearn-orange overflow-y-auto
        `}
      >
        <div className="flex flex-col h-full">
          {/* Top navigation section */}
          <div className="p-4 space-y-3 border-b-2 border-hooslearn-orange">
            {/* New Chat button */}
            <button
              onClick={handleNewChat}
              className="w-full flex items-center gap-3 px-4 py-3 bg-hooslearn-orange text-white 
                         rounded-lg hover:bg-hooslearn-orange-dark transition-all duration-200 font-medium"
            >
              <Plus size={20} />
              <span>{t("newChat")}</span>
            </button>

            {/* Search input - always visible */}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("searchChats")}
                className="w-full pl-10 pr-4 py-3 border-2 border-hooslearn-blue rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-hooslearn-blue focus:ring-offset-2
                           placeholder-gray-400 font-medium"
              />
              <Search
                size={20}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-hooslearn-blue"
              />
            </div>
          </div>

          {/* Chat history section - moved up, takes more space */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-hooslearn-blue font-wild-west text-lg mb-3">
              {searchQuery.trim()
                ? `${t("searchResults")} (${filteredChats.length})`
                : t("recentChats")}
            </h3>
            <div className="space-y-2">
              {filteredChats.map((chat, index) => (
                <div
                  key={chat.id}
                  onClick={() => handleChatClick(chat)}
                  className={`group relative p-3 rounded-lg transition-all duration-200 cursor-pointer
                    hover:bg-orange-50 text-hooslearn-blue ${
                      searchQuery.trim() && chat.title.toLowerCase().includes(searchQuery.toLowerCase()) && index < chats.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase())).length
                        ? "bg-orange-100 border-l-4 border-hooslearn-orange"
                        : ""
                    }`}
                >
                  <div className="flex items-start gap-2 min-w-0">
                    <MessageCircle
                      size={16}
                      className="mt-1 flex-shrink-0"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {localize(chat).title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {localize(chat).timestamp}
                      </p>
                    </div>
                  </div>

                  {/* Delete button on hover */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChat(chat.id);
                    }}
                    className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 
                               hover:bg-red-500 hover:text-white rounded"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {filteredChats.length === 0 && searchQuery.trim() && (
                <div className="text-center py-8 text-gray-500">
                  <MessageCircle size={48} className="mx-auto mb-2 opacity-50" />
                  <p>{t("noChatsFound")} "{searchQuery}"</p>
                </div>
              )}
            </div>
          </div>

          {/* Footer section */}
          <div className="p-4 border-t-2 border-hooslearn-orange">
            <p className="text-xs text-gray-500 text-center">
              {t("version")}
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};
