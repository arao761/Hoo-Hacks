import { useState, useEffect, useContext, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { OwlMascot } from "@/components/OwlMascot";
import { Music, Image, Video, Sparkles } from "lucide-react";
import { ChatContext } from "@/components/Layout";

export default function Index() {
  const [prompt, setPrompt] = useState("");
  const [selectedType, setSelectedType] = useState<"song" | "image" | "video" | null>(null);
  const [showOptions, setShowOptions] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const chatContext = useContext(ChatContext);
  const prevNewChatKeyRef = useRef(chatContext?.newChatKey || 0);

  useEffect(() => {
    if (chatContext && chatContext.newChatKey !== prevNewChatKeyRef.current) {
      // New chat triggered, clear the form
      setPrompt("");
      setSelectedType(null);
      setShowOptions(false);
      prevNewChatKeyRef.current = chatContext.newChatKey;
    }
  }, [chatContext?.newChatKey]);

  const handleSubmit = () => {
    if (prompt.trim()) {
      setShowOptions(true);
    }
  };

  const handleTypeSelect = (type: "song" | "image" | "video") => {
    setSelectedType(type);
  };

  const handleGenerateMedia = async () => {
    if (!prompt.trim() || !selectedType) return;
    setLoading(true);
    try {
      const res = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: prompt, output_type: selectedType }),
      });
      const { job_id } = await res.json();
      navigate(`/result/${job_id}?type=${selectedType}&topic=${encodeURIComponent(prompt)}`);
    } catch (err) {
      console.error("Failed to start generation", err);
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent default form submission behavior
      if (!showOptions && prompt.trim()) {
        handleSubmit();
      } else if (showOptions && selectedType) {
        handleGenerateMedia();
      }
    }
  };

  return (
    <div className="min-h-full bg-gradient-to-br from-hooslearn-orange-light via-white to-hooslearn-blue-light py-8 px-4 sm:px-6 lg:px-8">
      {/* Main container */}
      <div className="max-w-2xl mx-auto">
        {/* Header with logo and title */}
        <div className="text-center mb-8 sm:mb-12 lg:mb-16">
          {/* Owl Mascot */}
          <div className="flex justify-center mb-6 sm:mb-8">
            <div className="transform hover:scale-105 transition-transform duration-300">
              <OwlMascot size={160} />
            </div>
          </div>

          {/* App Title */}
          <h1 className="font-wild-west text-4xl sm:text-5xl lg:text-6xl text-hooslearn-blue mb-2">
            HoosLearn
          </h1>
          <p className="text-hooslearn-blue text-sm sm:text-base lg:text-lg font-medium tracking-wide">
            Learn Anything, Your Way!
          </p>
        </div>

        {/* Main content card */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8 lg:p-10 border-2 border-hooslearn-orange">
          {/* Section title */}
          <div className="text-center mb-6 sm:mb-8">
            <h2 className="font-wild-west text-2xl sm:text-3xl text-hooslearn-blue mb-2">
              What'll it be, Partner?
            </h2>
            <p className="text-hooslearn-blue text-sm sm:text-base opacity-80">
              Tell me what you want to learn, choose your style, and let's saddle up!
            </p>
          </div>

          {/* Prompt input */}
          <div className="mb-6">
            <div className="relative">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Prompt HoosLearn"
                className="w-full px-5 py-3 sm:py-4 text-sm sm:text-base border-2 border-hooslearn-orange rounded-full 
                           focus:outline-none focus:ring-2 focus:ring-hooslearn-orange focus:ring-offset-2 
                           transition-all duration-200 placeholder-gray-400 font-medium"
              />
              <Sparkles
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-hooslearn-orange pointer-events-none"
                size={20}
              />
            </div>
          </div>

          {/* Submit button */}
          <div className="mb-6">
            <button
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              className="w-full py-3 sm:py-4 bg-hooslearn-orange hover:bg-hooslearn-orange-dark 
                         disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-wild-west 
                         text-lg sm:text-xl rounded-full transition-all duration-200 
                         shadow-lg hover:shadow-xl transform hover:scale-105 disabled:hover:scale-100"
            >
              🤠 Let's Learn! 🤠
            </button>
          </div>

          {/* Content type selection - shown after clicking Let's Learn */}
          {showOptions && (
            <div className="mb-6">
              <p className="text-hooslearn-blue font-wild-west text-lg sm:text-xl mb-4 text-center">
                How do you wanna learn?
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Song option */}
                <button
                  onClick={() => handleTypeSelect("song")}
                  className={`p-6 sm:p-8 rounded-xl transition-all duration-200 flex flex-col items-center justify-center gap-3 
                             border-2 font-medium text-sm sm:text-base ${
                    selectedType === "song"
                      ? "bg-hooslearn-orange border-hooslearn-orange text-white shadow-lg scale-105"
                      : "bg-white border-hooslearn-orange text-hooslearn-blue hover:bg-orange-50"
                  }`}
                >
                  <Music size={32} />
                  <span className="font-wild-west text-lg">Song</span>
                </button>

                {/* Image option */}
                <button
                  onClick={() => handleTypeSelect("image")}
                  className={`p-6 sm:p-8 rounded-xl transition-all duration-200 flex flex-col items-center justify-center gap-3 
                             border-2 font-medium text-sm sm:text-base ${
                    selectedType === "image"
                      ? "bg-hooslearn-orange border-hooslearn-orange text-white shadow-lg scale-105"
                      : "bg-white border-hooslearn-orange text-hooslearn-blue hover:bg-orange-50"
                  }`}
                >
                  <Image size={32} />
                  <span className="font-wild-west text-lg">Image</span>
                </button>

                {/* Video option */}
                <button
                  onClick={() => handleTypeSelect("video")}
                  className={`p-6 sm:p-8 rounded-xl transition-all duration-200 flex flex-col items-center justify-center gap-3 
                             border-2 font-medium text-sm sm:text-base ${
                    selectedType === "video"
                      ? "bg-hooslearn-orange border-hooslearn-orange text-white shadow-lg scale-105"
                      : "bg-white border-hooslearn-orange text-hooslearn-blue hover:bg-orange-50"
                  }`}
                >
                  <Video size={32} />
                  <span className="font-wild-west text-lg">Video</span>
                </button>
              </div>

              {/* Generate Media button */}
              <div className="mt-6">
                <button
                  onClick={handleGenerateMedia}
                  disabled={!selectedType || loading}
                  className={`w-full py-3 sm:py-4 font-wild-west text-lg sm:text-xl rounded-full transition-all duration-200
                             shadow-lg hover:shadow-xl transform hover:scale-105 disabled:hover:scale-100 ${
                    selectedType && !loading
                      ? "bg-hooslearn-orange hover:bg-hooslearn-orange-dark text-white"
                      : "bg-gray-300 text-gray-500 cursor-not-allowed"
                  }`}
                >
                  {loading ? "Saddling up..." : "🎨 Generate Media 🎨"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer tagline */}
        <div className="text-center mt-8 sm:mt-12">
          <p className="font-wild-west text-hooslearn-blue text-sm sm:text-base">
            With HoosLearn, Education's Always in Style! 🎓
          </p>
        </div>
      </div>
    </div>
  );
}
