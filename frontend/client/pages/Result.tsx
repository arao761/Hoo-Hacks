import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { OwlMascot } from "@/components/OwlMascot";
import { Music, Image, Video, ArrowLeft, Loader2 } from "lucide-react";

type OutputType = "song" | "image" | "video";

interface ProgressEvent {
  event: string;
  message: string;
  cdn_url?: string;
}

const STEPS = ["prompted", "generating", "uploading", "done"];

export default function Result() {
  const { jobId } = useParams<{ jobId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const topic = searchParams.get("topic") ?? "";
  const outputType = (searchParams.get("type") ?? "song") as OutputType;

  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [cdnUrl, setCdnUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Try WebSocket first — use current host so this works in dev and prod
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/${jobId}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const data: ProgressEvent = JSON.parse(e.data);
      setEvents((prev) => [...prev, data]);
      if (data.event === "done" && data.cdn_url) {
        setCdnUrl(data.cdn_url);
      }
      if (data.event === "error") {
        setError(data.message);
      }
    };

    ws.onerror = () => {
      // WebSocket failed — fall back to HTTP polling
      ws.close();
      pollStatus();
    };

    return () => {
      ws.close();
    };
  }, [jobId]);

  // HTTP polling fallback
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollStatus = () => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/status/${jobId}`);
        const data = await res.json();
        if (data.status === "done") {
          clearInterval(pollRef.current!);
          setEvents((prev) => [...prev, { event: "done", message: "Ready!", cdn_url: data.cdn_url }]);
          setCdnUrl(data.cdn_url);
        } else if (data.status === "error") {
          clearInterval(pollRef.current!);
          setError(data.error_message ?? "Something went wrong.");
        }
      } catch {
        clearInterval(pollRef.current!);
        setError("Could not reach the server.");
      }
    }, 2000);
  };

  const currentStep = events.length > 0 ? events[events.length - 1].event : null;
  const isDone = currentStep === "done" && cdnUrl;
  const isError = !!error;

  const typeIcon = {
    song:  <Music  className="inline-block mr-2" size={20} />,
    image: <Image  className="inline-block mr-2" size={20} />,
    video: <Video  className="inline-block mr-2" size={20} />,
  }[outputType];

  return (
    <div className="min-h-full bg-gradient-to-br from-hooslearn-orange-light via-white to-hooslearn-blue-light py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">

        {/* Back button */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-hooslearn-blue font-medium mb-6 hover:underline"
        >
          <ArrowLeft size={16} /> Back
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <OwlMascot size={100} />
          </div>
          <h1 className="font-wild-west text-3xl sm:text-4xl text-hooslearn-blue mb-1">
            {typeIcon}{topic}
          </h1>
          <p className="text-hooslearn-blue opacity-70 text-sm capitalize">{outputType} generation</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8 border-2 border-hooslearn-orange">

          {/* Progress steps */}
          {!isDone && !isError && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                {STEPS.map((step, i) => {
                  const stepIndex  = STEPS.indexOf(currentStep ?? "");
                  const isDoneStep = i <= stepIndex;
                  return (
                    <div key={step} className="flex flex-col items-center gap-1 flex-1">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all
                        ${isDoneStep
                          ? "bg-hooslearn-orange border-hooslearn-orange text-white"
                          : "border-gray-300 text-gray-400"}`}>
                        {isDoneStep ? "✓" : i + 1}
                      </div>
                      <span className={`text-xs capitalize hidden sm:block ${isDoneStep ? "text-hooslearn-orange font-semibold" : "text-gray-400"}`}>
                        {step}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Latest message */}
              <div className="flex items-center justify-center gap-2 text-hooslearn-blue">
                <Loader2 className="animate-spin" size={18} />
                <span className="text-sm font-medium">
                  {events.length > 0 ? events[events.length - 1].message : "Waiting for the wrangler..."}
                </span>
              </div>
            </div>
          )}

          {/* Error state */}
          {isError && (
            <div className="text-center py-8">
              <p className="text-red-500 font-medium mb-4">Something went wrong: {error}</p>
              <button onClick={() => navigate("/")} className="text-hooslearn-blue underline">Try again</button>
            </div>
          )}

          {/* Result display */}
          {isDone && cdnUrl && (
            <div className="text-center">
              <p className="font-wild-west text-hooslearn-blue text-xl mb-6">Yeehaw, it's ready! 🤠</p>

              {outputType === "song" && (
                <div>
                  <audio controls className="w-full mb-4" src={cdnUrl}>
                    Your browser does not support audio playback.
                  </audio>
                </div>
              )}

              {outputType === "image" && (
                <img src={cdnUrl} alt={topic} className="w-full rounded-xl shadow-md mb-4" />
              )}

              {outputType === "video" && (
                <video controls className="w-full rounded-xl shadow-md mb-4" src={cdnUrl}>
                  Your browser does not support video playback.
                </video>
              )}

              <a
                href={cdnUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-2 text-sm text-hooslearn-blue underline"
              >
                Open in new tab ↗
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
