import { useState, useRef, useEffect } from 'react';
import ConversationalForm from './components/ConversationalForm';
import { FaLeaf } from 'react-icons/fa';
import { API_CONFIG } from './config/api';

function App() {
  const [readyFormulation, setReadyFormulation] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [formulationResult, setFormulationResult] = useState<any>(null);
  const [showStatusWindow, setShowStatusWindow] = useState(false);
  const [currentStatusIndex, setCurrentStatusIndex] = useState(0);
  const enrichedQueryRef = useRef<HTMLDivElement>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusStage, setStatusStage] = useState('');

  // Status messages for the animated status window
  const statusMessages = [
    'Enhancing your formulation request for clarity and precision...',
    'Consulting the AI for the most effective natural ingredients...',
    'Analyzing ingredient safety, compatibility, and efficacy...',
    'Finalizing your personalized formulation...'
  ];

  // Animate status window
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (showStatusWindow && isGenerating) {
      timer = setInterval(() => {
        setCurrentStatusIndex((prev) => (prev + 1) % statusMessages.length);
      }, 1500);
    }
    return () => clearInterval(timer);
  }, [showStatusWindow, isGenerating, statusMessages.length]);

  // Hide status window when done generating
  useEffect(() => {
    if (!isGenerating && showStatusWindow) {
      // Fade out after short delay
      const timeout = setTimeout(() => setShowStatusWindow(false), 800);
      return () => clearTimeout(timeout);
    }
  }, [isGenerating, showStatusWindow]);

  const handleFormulationReady = (enhancedQuery: string) => {
    setReadyFormulation(enhancedQuery);
    // Auto-scroll to the enriched query section
    setTimeout(() => {
      enrichedQueryRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }, 500);
  };

  const handleGenerateFormulation = async () => {
    if (!readyFormulation) return;
    setIsGenerating(true);
    setShowStatusWindow(true);
    setCurrentStatusIndex(0);
    setStatusMessage('');
    setStatusStage('');
    // Use SSE for real-time status updates
    const evtSource = new EventSource(`${API_CONFIG.FORMULATION_ENDPOINTS.STREAM}?query=${encodeURIComponent(readyFormulation)}`);
    evtSource.onopen = () => {
      console.log('SSE connection opened');
    };
    evtSource.onerror = (e) => {
      console.error('SSE error:', e);
    };
    evtSource.onmessage = (event) => {
      console.log('SSE event:', event.data);
      if (event.data) {
        try {
          const data = JSON.parse(event.data);
          setStatusStage(data.stage);
          setStatusMessage(data.message);
          if (data.stage === 'done') {
            evtSource.close();
            setTimeout(() => setShowStatusWindow(false), 1000);
          }
        } catch (err) {
          console.error('Failed to parse SSE data:', event.data, err);
        }
      }
    };
    try {
      const response = await fetch(API_CONFIG.FORMULATION_ENDPOINTS.GENERATE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: readyFormulation }),
      });
      if (!response.ok) throw new Error('Failed to generate formulation');
      const result = await response.json();
      setFormulationResult(result);
      setTimeout(() => {
        const resultsElement = document.querySelector('.formulation-results');
        resultsElement?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    } catch (error) {
      console.error('Error generating formulation:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // Formulation component definitions
  const formulationComponents = [
    {
      title: "Base Components",
      description: "Primary ingredients that form the foundation of your formulation",
      examples: "Water, oils, waxes, or other main carriers"
    },
    {
      title: "Active Ingredients",
      description: "Key functional ingredients that provide the main benefits",
      examples: "Vitamins, antioxidants, peptides, or botanical extracts"
    },
    {
      title: "Emollients & Humectants",
      description: "Ingredients that improve texture and moisture retention",
      examples: "Glycerin, shea butter, jojoba oil, or hyaluronic acid"
    },
    {
      title: "Preservatives & Stabilizers",
      description: "Ingredients that maintain product safety and shelf life",
      examples: "Natural preservatives, antioxidants, or pH stabilizers"
    },
    {
      title: "Enhancers & Additives",
      description: "Optional ingredients that improve performance or aesthetics",
      examples: "Fragrances, colorants, thickeners, or penetration enhancers"
    },
    {
      title: "Balancing Agents",
      description: "Ingredients that ensure proper formulation stability",
      examples: "pH adjusters, emulsifiers, or viscosity modifiers"
    }
  ];

  return (
    <div className="App">
      <header className="app-header gradient-hero">
        <div className="hero-content">
          <span className="hero-icon"><FaLeaf /></span>
          <h1>Scrtch.ai</h1>
          <p className="hero-tagline">Create clean, natural ingredient formulations in minutes </p>
        </div>
      </header>
      <main className="app-main">
        <div className="main-card">
          <ConversationalForm onFormulationReady={handleFormulationReady} />
          
          {readyFormulation && (
            <div className="enriched-query-section" ref={enrichedQueryRef}>
              <div className="enriched-header">
                <h3>What we understood..</h3>
                <p>Based on our conversation, here's your complete formulation request:</p>
              </div>
              
              <div className="enriched-query-container">
                <div className="enriched-query-content">
                  {readyFormulation}
                </div>
                <div className="enriched-actions">
                  <button 
                    className="copy-enriched-button"
                    onClick={() => navigator.clipboard.writeText(readyFormulation)}
                    title="Copy to clipboard"
                  >
                    Copy
                  </button>
                </div>
              </div>
              
              <div className="generate-section">
                <button 
                  className="generate-formulation-button"
                  onClick={handleGenerateFormulation}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <span className="loading-spinner"></span>
                      Generating Formulation...
                    </>
                  ) : (
                    <>
                       Generate Formulation
                    </>
                  )}
                </button>
                <p className="generate-hint">
                  Click to generate your natural ingredient formulation based on this request
                </p>
              </div>
            </div>
          )}
          {/* Status Window */}
          {showStatusWindow && (
            <>
              {console.log('StatusWindow:', statusStage, statusMessage)}
              <div className={`status-window${!isGenerating ? ' fade-out' : ''}`}>
                <div className="status-message">
                  <span className="status-typing">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </span>
                  {statusMessage || statusMessages[currentStatusIndex]}
                </div>
              </div>
            </>
          )}

          {formulationResult && (
            <div className="formulation-results">
              <div className="results-header">
                <h3>Your Natural Formulation</h3>
                <p>Here's your personalized formulation with natural ingredients:</p>
              </div>

              {/* Formulation Components Guide */}
              <div className="formulation-components-guide">
                <h4>📚 Formulation Fundamentals</h4>
                <p className="components-intro">
                  Every natural formulation consists of these essential components:
                </p>
                <div className="components-grid">
                  {formulationComponents.map((component, index) => (
                    <div key={index} className="component-card">
                      <div className="component-content">
                        <h5 className="component-title">{component.title}</h5>
                        <p className="component-description">{component.description}</p>
                        <div className="component-examples">
                          <span className="examples-label">Examples:</span> {component.examples}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="ingredients">
                <h4>Recommended Ingredients</h4>
                <div className="ingredient-feature-grid">
                  {formulationResult.ingredients.slice(0, 7).map((ingredient: any, index: number) => (
                    <div key={index} className="ingredient-feature-card">
                      <div className="ingredient-feature-name">{ingredient.name}</div>
                      <div className="ingredient-feature-details">
                        {ingredient.attributes.usage && (
                          <div className="ingredient-feature-usage">
                            <span className="feature-label">Usage:</span> {ingredient.attributes.usage}
                          </div>
                        )}
                        {ingredient.attributes.benefits && (
                          <div className="ingredient-feature-benefits">
                            <span className="feature-label">Benefits:</span> {ingredient.attributes.benefits}
                          </div>
                        )}
                        {ingredient.attributes.concentration && (
                          <div className="ingredient-feature-concentration">
                            <span className="feature-label">Concentration:</span> <span className="concentration-badge">{ingredient.attributes.concentration}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
      <footer className="app-footer minimal-footer">
        <p>Powered by Scrtch.ai • Natural Ingredients • Clean Formulations</p>
      </footer>
    </div>
  );
}

export default App; 