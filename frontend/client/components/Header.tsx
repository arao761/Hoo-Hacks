import { Check, ChevronDown, ChevronUp, LogIn, UserPlus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n, Language, LANGUAGES } from "@/i18n";

export const Header = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const navigate = useNavigate();
  const { lang, setLang, t } = useI18n();

  const subjects = [
    { name: t("subjects.math"), path: "/subject/math" },
    { name: t("subjects.science"), path: "/subject/science" },
    { name: t("subjects.history"), path: "/subject/history" },
    { name: t("subjects.english"), path: "/subject/english" },
    { name: t("subjects.coding"), path: "/subject/coding" },
  ];
  const languageItems = Object.entries(LANGUAGES) as [Language, string][];

  return (
    <header className="bg-white border-b-2 border-hooslearn-orange shadow-md">
      <div className="flex justify-between items-center px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center gap-2">
          <div
            className="text-hooslearn-blue font-wild-west text-xl sm:text-2xl cursor-pointer"
            onClick={() => navigate("/")}
          >
            {t("appName")}
          </div>
        </div>

        {/* Subject buttons in the center */}
        <div className="hidden md:flex items-center gap-2 lg:gap-4">
          {subjects.map((subject) => (
            <button
              key={subject.path}
              onClick={() => navigate(subject.path)}
              className="px-3 py-2 text-sm font-medium text-hooslearn-blue hover:text-hooslearn-orange
                         hover:bg-orange-50 rounded-lg transition-all duration-200"
            >
              {subject.name}
            </button>
          ))}
        </div>

        {/* Language dropdown + auth buttons on the right */}
        <div className="flex items-center gap-2 sm:gap-4 relative">
          <button
            onClick={() => setLangOpen((prev) => !prev)}
            className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-100 transition-all duration-200 text-sm"
          >
            {t("language")}: {LANGUAGES[lang]}
            {langOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {langOpen && (
            <div className="absolute right-0 top-full mt-2 w-40 z-20 bg-white border border-gray-200 rounded-lg shadow-lg">
              {languageItems.map(([code, label]) => (
                <button
                  key={code}
                  onClick={() => {
                    setLang(code);
                    setLangOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-gray-100 flex justify-between items-center text-sm"
                >
                  <span>{label}</span>
                  {lang === code && <Check size={14} className="text-hooslearn-orange" />}
                </button>
              ))}
            </div>
          )}
          {!isLoggedIn ? (
            <>
              <button
                onClick={() => setIsLoggedIn(true)}
                className="flex items-center gap-2 px-4 py-2 text-hooslearn-blue border-2 border-hooslearn-blue
                           rounded-lg hover:bg-blue-50 transition-all duration-200 text-sm sm:text-base font-medium"
              >
                <LogIn size={18} />
                <span className="hidden sm:inline">{t("login")}</span>
              </button>
              <button
                onClick={() => setIsLoggedIn(true)}
                className="flex items-center gap-2 px-4 py-2 bg-hooslearn-orange text-white
                           rounded-lg hover:bg-hooslearn-orange-dark transition-all duration-200
                           text-sm sm:text-base font-medium"
              >
                <UserPlus size={18} />
                <span className="hidden sm:inline">{t("signup")}</span>
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsLoggedIn(false)}
              className="flex items-center gap-2 px-4 py-2 bg-hooslearn-orange text-white
                         rounded-lg hover:bg-hooslearn-orange-dark transition-all duration-200
                         text-sm sm:text-base font-medium"
            >
              <span>{t("logout")}</span>
            </button>
          )}
        </div>
      </div>

      {/* Mobile subject buttons */}
      <div className="md:hidden border-t border-gray-200 px-4 py-2">
        <div className="flex justify-center gap-2 overflow-x-auto">
          {subjects.map((subject) => (
            <button
              key={subject.path}
              onClick={() => navigate(subject.path)}
              className="px-3 py-1 text-xs font-medium text-hooslearn-blue hover:text-hooslearn-orange
                         hover:bg-orange-50 rounded-md transition-all duration-200 whitespace-nowrap"
            >
              {subject.name}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};
