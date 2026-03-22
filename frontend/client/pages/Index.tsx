import { useState, useEffect, useContext, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { OwlMascot } from "@/components/OwlMascot";
import { Music, Video, Sparkles, BookOpen } from "lucide-react";
import { ChatContext } from "@/components/Layout";
import { useI18n } from "@/i18n";

export default function Index() {
  const { t, lang } = useI18n();
  const SUBJECTS = [
    { id: "math", name: t("subjects.math") },
    { id: "science", name: t("subjects.science") },
    { id: "history", name: t("subjects.history") },
    { id: "english", name: t("subjects.english") },
    { id: "coding", name: t("subjects.coding") },
  ];
  const [prompt, setPrompt] = useState("");
  const [selectedType, setSelectedType] = useState<"song" | "video" | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const chatContext = useContext(ChatContext);
  const prevNewChatKeyRef = useRef(chatContext?.newChatKey || 0);

  useEffect(() => {
    // Handle URL parameters for pre-filling prompt
    const subject = searchParams.get('subject');
    const concept = searchParams.get('concept');
    const subtopic = searchParams.get('subtopic');

    if (subject && concept) {
      let prefilledPrompt = `Teach me about ${concept}`;
      if (subtopic) {
        prefilledPrompt = `Teach me about ${subtopic} in ${concept}`;
      }
      setPrompt(prefilledPrompt);
    }
  }, [searchParams]);

  useEffect(() => {
    if (chatContext && chatContext.newChatKey !== prevNewChatKeyRef.current) {
      // New chat triggered, clear the form
      setPrompt("");
      setSelectedType(null);
      prevNewChatKeyRef.current = chatContext.newChatKey;
    }
  }, [chatContext?.newChatKey]);

  const handleTypeSelect = (type: "song" | "video") => {
    setSelectedType(type);
  };

  const handleGenerateMedia = async () => {
    if (!prompt.trim() || !selectedType) return;

    // Save to recent chats
    if (chatContext?.addChat) {
      chatContext.addChat({
        title: prompt.length > 30 ? prompt.substring(0, 30) + "..." : prompt,
        timestamp: "Just now",
      });
    }

    setLoading(true);
    try {
      const res = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: prompt, output_type: selectedType, language: lang }),
      });
      const { job_id } = await res.json();
      navigate(`/result/${job_id}?type=${selectedType}&topic=${encodeURIComponent(prompt)}`);
    } catch (err) {
      console.error("Failed to start generation", err);
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && prompt.trim() && selectedType) {
      e.preventDefault();
      handleGenerateMedia();
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
            {t("appName")}
          </h1>
          <p className="text-hooslearn-blue text-sm sm:text-base lg:text-lg font-medium tracking-wide">
            {t("tagline")}
          </p>
        </div>

        {/* Main content card */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8 lg:p-10 border-2 border-hooslearn-orange">
          {/* Section title */}
          <div className="text-center mb-6 sm:mb-8">
            <h2 className="font-wild-west text-2xl sm:text-3xl text-hooslearn-blue mb-2">
              {t("what")}
            </h2>
            <p className="text-hooslearn-blue text-sm sm:text-base opacity-80">
              {t("help")}
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
                placeholder={t("placeholder")}
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

          {/* Content type selection */}
          <div className="mb-6">
            <p className="text-hooslearn-blue font-wild-west text-lg sm:text-xl mb-4 text-center">
              {t("style")}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                <span className="font-wild-west text-lg">{t("song")}</span>
              </button>

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
                <span className="font-wild-west text-lg">{t("video")}</span>
              </button>
            </div>
          </div>

          {/* Single Let's Learn button */}
          <div className="mb-2">
            <button
              onClick={handleGenerateMedia}
              disabled={!prompt.trim() || !selectedType || loading}
              className={`w-full py-3 sm:py-4 font-wild-west text-lg sm:text-xl rounded-full transition-all duration-200
                         shadow-lg hover:shadow-xl transform hover:scale-105 disabled:hover:scale-100 ${
                prompt.trim() && selectedType && !loading
                  ? "bg-hooslearn-orange hover:bg-hooslearn-orange-dark text-white"
                  : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }`}
            >
              {loading ? t("loading") : t("start")}
            </button>
          </div>
        </div>

        {/* Browse by Subject */}
        <div className="mt-8">
          <div className="text-center mb-4">
            <h3 className="font-wild-west text-xl text-hooslearn-blue flex items-center justify-center gap-2">
              <BookOpen size={20} /> {t("browseBySubject")}
            </h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {SUBJECTS.map((subject) => (
              <button
                key={subject.id}
                onClick={() => navigate(`/subject/${subject.id}`)}
                className="py-3 px-4 bg-white border-2 border-hooslearn-blue text-hooslearn-blue font-wild-west
                           rounded-xl hover:bg-hooslearn-blue hover:text-white transition-all duration-200
                           shadow-sm hover:shadow-md text-sm sm:text-base"
              >
                {subject.name}
              </button>
            ))}
          </div>
        </div>

        {/* Footer tagline */}
        <div className="text-center mt-8 sm:mt-12">
          <p className="font-wild-west text-hooslearn-blue text-sm sm:text-base">
            {t("footer")}
          </p>
        </div>
      </div>
    </div>
  );
}
