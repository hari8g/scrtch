import { useState, useEffect } from 'react'
import { generateFormulation, validateQuery, getQuerySuggestions, FormulationResponse, QueryValidationResponse } from '../services/api'

interface FormulationFormProps {
  initialQuery?: string;
}

function FormulationForm({ initialQuery = '' }: FormulationFormProps) {
  const [query, setQuery] = useState(initialQuery)
  const [formulationResult, setFormulationResult] = useState<FormulationResponse | null>(null)
  const [validationResult, setValidationResult] = useState<QueryValidationResponse | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Update query when initialQuery prop changes
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery)
      handleQueryChange(initialQuery)
    }
  }, [initialQuery])

  const handleQueryChange = async (newQuery: string) => {
    setQuery(newQuery)
    
    if (newQuery.trim().length > 10) {
      try {
        // Validate query as user types
        const validation = await validateQuery(newQuery)
        setValidationResult(validation)
        
        // Get suggestions if query needs improvement
        if (!validation.is_sufficient) {
          const querySuggestions = await getQuerySuggestions(newQuery)
          setSuggestions(querySuggestions)
        } else {
          setSuggestions([])
        }
      } catch (err) {
        console.error('Query validation failed:', err)
      }
    } else {
      setValidationResult(null)
      setSuggestions([])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError('')
    
    try {
      const result = await generateFormulation(query)
      setFormulationResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate formulation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="formulation-form">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="query">Describe your formulation needs:</label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            placeholder="e.g., natural skincare for sensitive skin, organic hair care, etc."
            rows={4}
            required
          />
        </div>
        
        {/* Query Validation Display */}
        {validationResult && (
          <div className={`validation-result ${validationResult.is_sufficient ? 'valid' : 'invalid'}`}>
            <div className="validation-header">
              <span className={`status ${validationResult.is_sufficient ? 'success' : 'warning'}`}>
                {validationResult.is_sufficient ? '✓ Query Ready' : '⚠ Query Needs Improvement'}
              </span>
              <span className="confidence">
                Confidence: {Math.round(validationResult.confidence_score * 100)}%
              </span>
            </div>
            
            {!validationResult.is_sufficient && (
              <div className="missing-info">
                <h4>Missing Information:</h4>
                <ul>
                                  {validationResult.missing_information.map((info: string, index: number) => (
                  <li key={index}>{info}</li>
                ))}
                </ul>
              </div>
            )}
            
            {suggestions.length > 0 && (
              <div className="suggestions">
                <h4>Suggestions:</h4>
                <ul>
                  {suggestions.map((suggestion, index) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        <button type="submit" disabled={loading || (validationResult ? !validationResult.is_sufficient : false)}>
          {loading ? 'Generating...' : 'Generate Formulation'}
        </button>
      </form>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {formulationResult && (
        <div className="formulation-results">
          <div className="query-analysis">
            <h2>Query Analysis</h2>
            <div className="analysis-grid">
              <div className="analysis-item">
                <h4>Original Query</h4>
                <p>{formulationResult.original_query}</p>
              </div>
              <div className="analysis-item">
                <h4>Enhanced Query</h4>
                <p>{formulationResult.enhanced_query}</p>
              </div>
            </div>
          </div>

          <div className="ingredients">
            <h2>Generated Ingredients</h2>
            <div className="ingredients-grid">
              {formulationResult.ingredients.map((ingredient: any, index: number) => (
                <div key={index} className="ingredient-card">
                  <h3>{ingredient.name}</h3>
                  <div className="attributes">
                    {Object.entries(ingredient.attributes).map(([key, value]) => (
                      <div key={key} className="attribute">
                        <strong>{key}:</strong> {String(value)}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FormulationForm 