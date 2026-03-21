import { useState } from "react";
import { Menu, X, Plus, Search, Folder, Zap, MessageCircle, Trash2 } from "lucide-react";

export interface ChatItem {
  id: string;
  title: string;
  timestamp: string;
}

interface SidebarProps {
  isMobile?: boolean;
  onNewChat: () => void;
}

export const Sidebar = ({ isMobile = false, onNewChat }: SidebarProps) => {
  const [isOpen, setIsOpen] = useState(!isMobile);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
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

  const handleNewChat = () => {
    onNewChat();
  };

  const handleSearchClick = () => {
    setIsSearching(true);
  };

  const handleSearchBlur = () => {
    if (!searchQuery.trim()) {
      setIsSearching(false);
    }
  };

  const handleDeleteChat = (chatId: string) => {
    setChats(chats.filter(chat => chat.id !== chatId));
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
              <span>New Chat</span>
            </button>

            {/* Search button/input */}
            {!isSearching ? (
              <button
                onClick={handleSearchClick}
                className="w-full flex items-center gap-3 px-4 py-3 border-2 border-hooslearn-blue 
                           text-hooslearn-blue rounded-lg hover:bg-blue-50 transition-all duration-200 font-medium cursor-text"
              >
                <Search size={20} />
                <span>Search Chats</span>
              </button>
            ) : (
              <input
                type="text"
                autoFocus
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onBlur={handleSearchBlur}
                placeholder="Search chats..."
                className="w-full px-4 py-3 border-2 border-hooslearn-blue rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-hooslearn-blue focus:ring-offset-2
                           placeholder-gray-400 font-medium"
              />
            )}
          </div>

          {/* Menu items section */}
          <div className="p-4 space-y-2 border-b-2 border-hooslearn-orange">
            <button
              className="w-full flex items-center gap-3 px-4 py-3 text-hooslearn-blue 
                         hover:bg-orange-50 rounded-lg transition-all duration-200 font-medium text-left"
            >
              <Folder size={20} />
              <span>Projects</span>
            </button>

            <button
              className="w-full flex items-center gap-3 px-4 py-3 text-hooslearn-blue 
                         hover:bg-orange-50 rounded-lg transition-all duration-200 font-medium text-left"
            >
              <Zap size={20} />
              <span>Artifacts</span>
            </button>
          </div>

          {/* Chat history section */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-hooslearn-blue font-wild-west text-lg mb-3">
              Recent Chats
            </h3>
            <div className="space-y-2">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group relative p-3 rounded-lg transition-all duration-200 cursor-pointer
                    hover:bg-orange-50 text-hooslearn-blue`}
                >
                  <div className="flex items-start gap-2 min-w-0">
                    <MessageCircle
                      size={16}
                      className="mt-1 flex-shrink-0"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {chat.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {chat.timestamp}
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
            </div>
          </div>

          {/* Footer section */}
          <div className="p-4 border-t-2 border-hooslearn-orange">
            <p className="text-xs text-gray-500 text-center">
              HoosLearn v1.0
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};
