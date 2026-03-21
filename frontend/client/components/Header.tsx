import { LogIn, UserPlus } from "lucide-react";
import { useState } from "react";

export const Header = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  return (
    <header className="bg-white border-b-2 border-hooslearn-orange shadow-md">
      <div className="flex justify-between items-center px-4 sm:px-6 lg:px-8 py-4">
        {/* Logo on the left - could be clickable to go home */}
        <div className="flex items-center gap-2">
          <div className="text-hooslearn-blue font-wild-west text-xl sm:text-2xl">
            HoosLearn
          </div>
        </div>

        {/* Auth buttons on the right */}
        <div className="flex items-center gap-3 sm:gap-4">
          {!isLoggedIn ? (
            <>
              <button
                onClick={() => setIsLoggedIn(true)}
                className="flex items-center gap-2 px-4 py-2 text-hooslearn-blue border-2 border-hooslearn-blue 
                           rounded-lg hover:bg-blue-50 transition-all duration-200 text-sm sm:text-base font-medium"
              >
                <LogIn size={18} />
                <span className="hidden sm:inline">Log In</span>
              </button>
              <button
                onClick={() => setIsLoggedIn(true)}
                className="flex items-center gap-2 px-4 py-2 bg-hooslearn-orange text-white 
                           rounded-lg hover:bg-hooslearn-orange-dark transition-all duration-200 
                           text-sm sm:text-base font-medium"
              >
                <UserPlus size={18} />
                <span className="hidden sm:inline">Sign Up</span>
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsLoggedIn(false)}
              className="flex items-center gap-2 px-4 py-2 bg-hooslearn-orange text-white 
                         rounded-lg hover:bg-hooslearn-orange-dark transition-all duration-200 
                         text-sm sm:text-base font-medium"
            >
              <span>Logout</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
