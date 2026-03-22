import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, BookOpen, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { useI18n } from "@/i18n";

const subjectData = {
  Math: [
    "Algebra Basics",
    "Geometry Fundamentals",
    "Calculus Introduction",
    "Statistics & Probability",
    "Trigonometry",
    "Number Theory",
    "Linear Algebra",
    "Discrete Mathematics"
  ],
  Science: [
    "Physics Fundamentals",
    "Chemistry Basics",
    "Biology Essentials",
    "Earth Science",
    "Astronomy",
    "Environmental Science",
    "Anatomy & Physiology",
    "Ecology"
  ],
  History: [
    "Ancient Civilizations",
    "World War History",
    "American History",
    "European History",
    "Asian History",
    "African History",
    "Modern History",
    "Archaeology"
  ],
  English: [
    "Grammar & Syntax",
    "Literature Analysis",
    "Writing Skills",
    "Poetry & Prose",
    "Shakespeare Studies",
    "Creative Writing",
    "Journalism",
    "Language Evolution"
  ],
  Coding: [
    "Python Programming",
    "JavaScript Fundamentals",
    "Web Development",
    "Data Structures",
    "Algorithms",
    "Machine Learning",
    "Database Design",
    "Software Engineering"
  ]
};

const subtopicsData: Record<string, Record<string, string[]>> = {
  Math: {
    "Algebra Basics": [
      "Variables and Expressions",
      "Solving Linear Equations",
      "Inequalities",
      "Systems of Equations",
      "Quadratic Equations",
      "Polynomials",
      "Rational Expressions",
      "Radical Expressions"
    ],
    "Geometry Fundamentals": [
      "Points, Lines, and Planes",
      "Angles and Angle Relationships",
      "Triangles and Their Properties",
      "Quadrilaterals",
      "Circles and Circumference",
      "Area and Perimeter",
      "Volume of 3D Shapes",
      "Coordinate Geometry"
    ],
    "Calculus Introduction": [
      "Limits and Continuity",
      "Derivatives",
      "Applications of Derivatives",
      "Integrals",
      "Fundamental Theorem",
      "Techniques of Integration",
      "Applications of Integrals",
      "Series and Sequences"
    ],
    "Statistics & Probability": [
      "Descriptive Statistics",
      "Data Visualization",
      "Probability Basics",
      "Random Variables",
      "Normal Distribution",
      "Sampling Methods",
      "Hypothesis Testing",
      "Regression Analysis"
    ],
    "Trigonometry": [
      "Right Triangle Trigonometry",
      "Unit Circle",
      "Trigonometric Identities",
      "Graphing Trigonometric Functions",
      "Inverse Trigonometric Functions",
      "Law of Sines and Cosines",
      "Polar Coordinates",
      "Complex Numbers"
    ],
    "Number Theory": [
      "Divisibility Rules",
      "Prime Numbers",
      "Greatest Common Divisor",
      "Least Common Multiple",
      "Modular Arithmetic",
      "Diophantine Equations",
      "Cryptography Basics",
      "Number Systems"
    ],
    "Linear Algebra": [
      "Vectors and Vector Spaces",
      "Matrices and Operations",
      "Determinants",
      "Eigenvalues and Eigenvectors",
      "Linear Transformations",
      "Systems of Linear Equations",
      "Vector Spaces",
      "Inner Product Spaces"
    ],
    "Discrete Mathematics": [
      "Logic and Proofs",
      "Sets and Functions",
      "Combinatorics",
      "Graph Theory",
      "Boolean Algebra",
      "Number Theory Applications",
      "Algorithms and Complexity",
      "Cryptography"
    ]
  },
  Science: {
    "Physics Fundamentals": [
      "Motion and Forces",
      "Energy and Work",
      "Electricity and Magnetism",
      "Waves and Sound",
      "Light and Optics",
      "Thermodynamics",
      "Quantum Physics",
      "Nuclear Physics"
    ],
    "Chemistry Basics": [
      "Atomic Structure",
      "Periodic Table",
      "Chemical Bonding",
      "Chemical Reactions",
      "Stoichiometry",
      "Solutions and Mixtures",
      "Acids and Bases",
      "Organic Chemistry"
    ],
    "Biology Essentials": [
      "Cell Structure and Function",
      "Genetics and Heredity",
      "Evolution and Natural Selection",
      "Ecosystems and Ecology",
      "Human Anatomy",
      "Microorganisms",
      "Plant Biology",
      "Animal Behavior"
    ],
    "Earth Science": [
      "Geology and Rocks",
      "Weather and Climate",
      "Oceanography",
      "Atmospheric Science",
      "Plate Tectonics",
      "Natural Disasters",
      "Earth's Resources",
      "Environmental Geology"
    ],
    "Astronomy": [
      "Solar System",
      "Stars and Galaxies",
      "Cosmology",
      "Telescopes and Observatories",
      "Planetary Science",
      "Stellar Evolution",
      "Black Holes",
      "Astrophysics"
    ],
    "Environmental Science": [
      "Ecosystems",
      "Biodiversity",
      "Climate Change",
      "Pollution and Waste",
      "Conservation Biology",
      "Sustainable Development",
      "Environmental Policy",
      "Natural Resource Management"
    ],
    "Anatomy & Physiology": [
      "Human Body Systems",
      "Cardiovascular System",
      "Respiratory System",
      "Digestive System",
      "Nervous System",
      "Muscular System",
      "Skeletal System",
      "Endocrine System"
    ],
    "Ecology": [
      "Population Ecology",
      "Community Ecology",
      "Ecosystem Ecology",
      "Biomes",
      "Food Webs",
      "Energy Flow",
      "Nutrient Cycling",
      "Ecological Succession"
    ]
  },
  History: {
    "Ancient Civilizations": [
      "Mesopotamia",
      "Ancient Egypt",
      "Indus Valley Civilization",
      "Ancient China",
      "Ancient Greece",
      "Ancient Rome",
      "Maya Civilization",
      "Olmec Civilization"
    ],
    "World War History": [
      "World War I Causes",
      "World War I Battles",
      "World War II Causes",
      "World War II European Theater",
      "World War II Pacific Theater",
      "Holocaust",
      "Cold War",
      "Nuclear Age"
    ],
    "American History": [
      "Colonial America",
      "American Revolution",
      "Constitutional Convention",
      "Civil War",
      "Industrial Revolution",
      "Civil Rights Movement",
      "Modern America",
      "American Foreign Policy"
    ],
    "European History": [
      "Renaissance",
      "Age of Exploration",
      "Enlightenment",
      "French Revolution",
      "Industrial Revolution",
      "World Wars",
      "European Union",
      "Cold War Europe"
    ],
    "Asian History": [
      "Ancient Asian Civilizations",
      "Chinese Dynasties",
      "Japanese History",
      "Indian History",
      "Southeast Asian History",
      "Modern Asian History",
      "Asian Colonialism",
      "Asian Economic Development"
    ],
    "African History": [
      "Ancient African Kingdoms",
      "African Slave Trade",
      "Colonial Africa",
      "African Independence",
      "Apartheid",
      "Modern African Politics",
      "African Economic Development",
      "African Cultural Heritage"
    ],
    "Modern History": [
      "Industrial Revolution",
      "World Wars",
      "Cold War",
      "Decolonization",
      "Civil Rights Movements",
      "Space Race",
      "Digital Revolution",
      "Globalization"
    ],
    "Archaeology": [
      "Archaeological Methods",
      "Ancient Artifacts",
      "Excavation Techniques",
      "Dating Methods",
      "Cultural Preservation",
      "Underwater Archaeology",
      "Forensic Archaeology",
      "Digital Archaeology"
    ]
  },
  English: {
    "Grammar & Syntax": [
      "Parts of Speech",
      "Sentence Structure",
      "Subject-Verb Agreement",
      "Tense and Aspect",
      "Active and Passive Voice",
      "Punctuation",
      "Word Order",
      "Common Grammar Mistakes"
    ],
    "Literature Analysis": [
      "Literary Devices",
      "Character Analysis",
      "Plot Structure",
      "Theme and Symbolism",
      "Point of View",
      "Tone and Mood",
      "Literary Criticism",
      "Comparative Literature"
    ],
    "Writing Skills": [
      "Essay Writing",
      "Research Papers",
      "Creative Writing",
      "Technical Writing",
      "Business Writing",
      "Academic Writing",
      "Journalism Writing",
      "Copywriting"
    ],
    "Poetry & Prose": [
      "Poetic Forms",
      "Poetic Devices",
      "Prose Fiction",
      "Literary Genres",
      "Narrative Techniques",
      "Stylistic Analysis",
      "Poetry Analysis",
      "Creative Writing Techniques"
    ],
    "Shakespeare Studies": [
      "Shakespeare's Life",
      "Elizabethan Theater",
      "Shakespeare's Plays",
      "Shakespeare's Sonnets",
      "Shakespearean Language",
      "Shakespeare Adaptations",
      "Shakespeare Criticism",
      "Shakespeare in Modern Times"
    ],
    "Creative Writing": [
      "Fiction Writing",
      "Poetry Writing",
      "Screenwriting",
      "Playwriting",
      "Creative Nonfiction",
      "Writing Workshops",
      "Publishing Process",
      "Writer's Craft"
    ],
    "Journalism": [
      "News Writing",
      "Feature Writing",
      "Investigative Journalism",
      "Digital Journalism",
      "Broadcast Journalism",
      "Photojournalism",
      "Media Ethics",
      "Journalism Law"
    ],
    "Language Evolution": [
      "Language Origins",
      "Language Families",
      "Historical Linguistics",
      "Language Change",
      "Dialects and Accents",
      "Language Preservation",
      "Language Technology",
      "Sociolinguistics"
    ]
  },
  Coding: {
    "Python Programming": [
      "Python Basics",
      "Data Types and Variables",
      "Control Structures",
      "Functions and Modules",
      "Object-Oriented Programming",
      "File Handling",
      "Error Handling",
      "Python Libraries"
    ],
    "JavaScript Fundamentals": [
      "JavaScript Basics",
      "DOM Manipulation",
      "Event Handling",
      "Asynchronous Programming",
      "ES6+ Features",
      "JavaScript Frameworks",
      "Node.js",
      "Web APIs"
    ],
    "Web Development": [
      "HTML Fundamentals",
      "CSS Styling",
      "Responsive Design",
      "JavaScript for Web",
      "Frontend Frameworks",
      "Backend Development",
      "Database Integration",
      "Web Security"
    ],
    "Data Structures": [
      "Arrays and Lists",
      "Stacks and Queues",
      "Trees and Graphs",
      "Hash Tables",
      "Heaps",
      "Sorting Algorithms",
      "Searching Algorithms",
      "Time Complexity"
    ],
    "Algorithms": [
      "Algorithm Analysis",
      "Sorting Algorithms",
      "Searching Algorithms",
      "Dynamic Programming",
      "Greedy Algorithms",
      "Graph Algorithms",
      "String Algorithms",
      "Optimization Problems"
    ],
    "Machine Learning": [
      "Machine Learning Basics",
      "Supervised Learning",
      "Unsupervised Learning",
      "Neural Networks",
      "Deep Learning",
      "Natural Language Processing",
      "Computer Vision",
      "ML Ethics"
    ],
    "Database Design": [
      "Relational Databases",
      "SQL Fundamentals",
      "Database Normalization",
      "NoSQL Databases",
      "Database Indexing",
      "Query Optimization",
      "Database Security",
      "Big Data"
    ],
    "Software Engineering": [
      "Software Development Life Cycle",
      "Agile Methodology",
      "Version Control",
      "Testing Strategies",
      "Code Quality",
      "Design Patterns",
      "Software Architecture",
      "DevOps Practices"
    ]
  }
};

export default function Subject() {
  const { subject } = useParams<{ subject: string }>();
  const navigate = useNavigate();
  const { t } = useI18n();

  const SUBJECT_SLUG_TO_KEY: Record<string, keyof typeof subjectData> = {
    math: "Math",
    science: "Science",
    history: "History",
    english: "English",
    coding: "Coding",
  };

  const subjectKey = subject?.toLowerCase() || "";
  const mappedSubjectKey = SUBJECT_SLUG_TO_KEY[subjectKey];
  const subjectTitle = subjectKey ? t(`subjects.${subjectKey}`) : "";
  const [openDropdowns, setOpenDropdowns] = useState<Record<number, boolean>>({});

  const toggleDropdown = (index: number) => {
    setOpenDropdowns(prev => {
      const currentlyOpen = prev[index];
      if (currentlyOpen) {
        // If currently open, just close it
        return {
          ...prev,
          [index]: false
        };
      } else {
        // If closed, close all others and open this one
        const newState: Record<number, boolean> = {};
        newState[index] = true;
        return newState;
      }
    });
  };

  const slugify = (text: string) =>
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");

  const translateSubjectString = (text: string) => {
    if (!subjectKey) return text;

    const key = `subjectContent.${subjectKey}.${slugify(text)}`;
    const translated = t(key);

    return translated === key ? text : translated;
  };

  const handleSubtopicClick = (concept: string, subtopic: string) => {
    navigate(`/?subject=${subjectKey}&concept=${encodeURIComponent(concept)}&subtopic=${encodeURIComponent(subtopic)}`);
  };

  if (!subject || !mappedSubjectKey) {
    return (
      <div className="min-h-full bg-gradient-to-br from-hooslearn-orange-light via-white to-hooslearn-blue-light py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="font-wild-west text-4xl text-hooslearn-blue mb-4">{t("subjectNotFound")}</h1>
          <button
            onClick={() => navigate('/')}
            className="bg-hooslearn-orange text-white px-6 py-3 rounded-lg hover:bg-hooslearn-orange-dark transition-colors"
          >
            {t("goHome")}
          </button>
        </div>
      </div>
    );
  }

  const concepts = subjectData[mappedSubjectKey];

  return (
    <div className="min-h-full bg-gradient-to-br from-hooslearn-orange-light via-white to-hooslearn-blue-light py-8 px-4 sm:px-6 lg:px-8">
      {/* Main container */}
      <div className="max-w-4xl mx-auto">
        {/* Header with back button */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-hooslearn-blue hover:text-hooslearn-orange transition-colors mb-4"
          >
            <ArrowLeft size={20} />
            <span>{t("backToHome")}</span>
          </button>

          <div className="text-center">
            <h1 className="font-wild-west text-4xl sm:text-5xl lg:text-6xl text-hooslearn-blue mb-2">
              {subjectTitle || subject}
            </h1>
            <p className="text-hooslearn-blue text-lg font-medium">
              {t("chooseConcept")}
            </p>
          </div>
        </div>

        {/* Concepts grid */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8 lg:p-10 border-2 border-hooslearn-orange">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-start">
            {concepts.map((concept, index) => {
              const isOpen = openDropdowns[index] || false;
              const subtopics = subtopicsData[mappedSubjectKey]?.[concept] || [];

              return (
                <div
                  key={index}
                  className="bg-gradient-to-br from-white to-orange-50 border-2 border-hooslearn-orange
                           rounded-xl overflow-hidden shadow-sm"
                >
                  {/* Concept header - clickable to toggle dropdown */}
                  <button
                    onClick={() => toggleDropdown(index)}
                    className="w-full p-4 bg-gradient-to-r from-hooslearn-orange to-hooslearn-orange-dark
                             text-white hover:from-hooslearn-orange-dark hover:to-hooslearn-orange
                             transition-all duration-200 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <BookOpen size={20} />
                      <h3 className="font-wild-west text-lg text-left">
                        {translateSubjectString(concept)}
                      </h3>
                    </div>
                    {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </button>

                  {/* Dropdown content */}
                  {isOpen && (
                    <div className="bg-white border-t border-hooslearn-orange">
                      <div className="max-h-64 overflow-y-auto">
                        {subtopics.map((subtopic, subIndex) => (
                          <button
                            key={subIndex}
                            onClick={() => handleSubtopicClick(concept, subtopic)}
                            className="w-full p-3 text-left hover:bg-orange-50 transition-colors
                                     border-b border-gray-100 last:border-b-0 flex items-center gap-2
                                     text-hooslearn-blue hover:text-hooslearn-orange"
                          >
                            <Sparkles size={14} className="text-hooslearn-orange flex-shrink-0" />
                            <span className="text-sm font-medium">{translateSubjectString(subtopic)}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="font-wild-west text-hooslearn-blue text-sm">
            {t("clickToExplore")}
          </p>
        </div>
      </div>
    </div>
  );
}