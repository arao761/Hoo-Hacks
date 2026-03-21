export const OwlMascot = ({ size = 200 }: { size?: number }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="drop-shadow-lg"
    >
      {/* Cowboy Hat */}
      <g>
        {/* Hat brim front */}
        <ellipse cx="100" cy="45" rx="95" ry="20" fill="#8B4513" />
        
        {/* Hat brim shadow */}
        <ellipse cx="100" cy="46" rx="92" ry="18" fill="#6B3410" opacity="0.5" />
        
        {/* Hat crown left */}
        <path
          d="M 60 45 Q 60 20 80 12 L 85 40 Z"
          fill="#A0522D"
        />
        
        {/* Hat crown center */}
        <path
          d="M 80 12 Q 100 5 120 12 L 115 40 L 85 40 Z"
          fill="#C85A54"
        />
        
        {/* Hat crown right */}
        <path
          d="M 120 12 Q 140 20 140 45 L 115 40 Z"
          fill="#A0522D"
        />
        
        {/* Hat band */}
        <rect x="55" y="44" width="90" height="8" fill="#FF8C00" rx="2" />
        
        {/* Hat band shine */}
        <ellipse cx="100" cy="48" rx="40" ry="2" fill="#FFB347" opacity="0.6" />
        
        {/* Hat band buckle */}
        <rect x="96" y="44" width="8" height="10" fill="#FFD700" />
      </g>

      {/* Owl Head */}
      <g>
        {/* Head circle */}
        <circle cx="100" cy="110" r="50" fill="#1B3A5C" />
        
        {/* Head highlight */}
        <ellipse cx="90" cy="100" rx="20" ry="25" fill="#2C5282" opacity="0.7" />

        {/* Left ear tuft */}
        <path
          d="M 60 75 Q 50 60 55 45"
          stroke="#0F1F30"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
        />

        {/* Right ear tuft */}
        <path
          d="M 140 75 Q 150 60 145 45"
          stroke="#0F1F30"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
        />

        {/* Left eye white */}
        <circle cx="75" cy="100" r="18" fill="#FFFFFF" />
        
        {/* Right eye white */}
        <circle cx="125" cy="100" r="18" fill="#FFFFFF" />

        {/* Left eye iris */}
        <circle cx="75" cy="102" r="12" fill="#FF8C00" />
        
        {/* Right eye iris */}
        <circle cx="125" cy="102" r="12" fill="#FF8C00" />

        {/* Left eye pupil */}
        <circle cx="76" cy="98" r="7" fill="#000000" />
        
        {/* Right eye pupil */}
        <circle cx="126" cy="98" r="7" fill="#000000" />

        {/* Left eye shine */}
        <circle cx="78" cy="96" r="3" fill="#FFFFFF" />
        
        {/* Right eye shine */}
        <circle cx="128" cy="96" r="3" fill="#FFFFFF" />

        {/* Beak */}
        <path
          d="M 100 115 L 95 130 L 105 130 Z"
          fill="#FF8C00"
        />

        {/* Beak shine */}
        <path
          d="M 100 115 L 97 125 L 100 123 Z"
          fill="#FFB347"
          opacity="0.8"
        />

        {/* Chest/belly circle */}
        <circle cx="100" cy="140" r="35" fill="#2C5282" />
        
        {/* Belly lighter shade */}
        <ellipse cx="100" cy="145" rx="28" ry="30" fill="#4A7BA7" opacity="0.6" />
      </g>

      {/* Wings */}
      <g>
        {/* Left wing */}
        <ellipse cx="60" cy="125" rx="22" ry="38" fill="#0F1F30" transform="rotate(-25 60 125)" />
        
        {/* Right wing */}
        <ellipse cx="140" cy="125" rx="22" ry="38" fill="#0F1F30" transform="rotate(25 140 125)" />
      </g>

      {/* Feet */}
      <g>
        {/* Left foot */}
        <path d="M 80 175 L 70 200 L 75 200 M 80 175 L 80 200 M 80 175 L 90 200 M 85 200 L 85 210" 
              stroke="#FF8C00" strokeWidth="4" fill="none" strokeLinecap="round" />
        
        {/* Right foot */}
        <path d="M 120 175 L 110 200 L 115 200 M 120 175 L 120 200 M 120 175 L 130 200 M 125 200 L 125 210" 
              stroke="#FF8C00" strokeWidth="4" fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
};
