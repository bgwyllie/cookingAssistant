import React, { useState } from 'react'
import './App.css';

function App() {
  const [ingredientsInput, setIngredientsInput] = useState('')
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const ingredients = ingredientsInput.trim()
    if(!ingredients) {
      setError("Please enter at least one ingredient")
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/find_recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ingredients, top_k: 3})
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || response.statusText)
      }
      const data = await response.json()
      setRecipes(data.results)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="recipe-search">
        <h2 className="title">Find Recipes For Your Ingredients and Requirements</h2>
        <form onSubmit={handleSubmit}>
          <div class="recipe-search-bar">
            <input
              type="text"
              value={ingredientsInput}
              onChange={(e) => setIngredientsInput(e.target.value)}
              placeholder="Enter recipe requirements, e.g. tofu, garlic, vegetarian"
              className="search-control"
              disabled={loading}
            />
          </div>
          <button type="submit" class="search-bar-button" disabled={loading}>
            {loading ? 'Searching...' : 'Find Recipes'}
          </button>
        </form>
      {error && <p style={{color:"red"}}>{error}</p>}
      <div className="recipe-result">
        <h2 className="title">Recipe Suggestions:</h2>
        <div className="recipe">
        {recipes.map((r, idx) => (
          <div key={idx} className="recipe-card">
            <h3><a href={r.url} target="_blank" rel="noopener noreferrer" className="recipe-name">{r.title}</a></h3>
            <p>Cook time: {r.cook_time_mins} mins</p>
            <div className="recipe-instructions">
              <summary><b><em>Ingredients</em></b></summary>
              <ul className="ingredients">{r.ingredients.map((ing,i)=><li key={i}>{ing}</li>)}</ul>
              <summary><b><em>Steps</em></b></summary>
              <ol className="steps">{r.steps.map((st,i)=><li key={i}>{st}</li>)}</ol>
              <summary><b><em>Tools</em></b></summary>
              <ul className="tools">{r.tools.map((tool,i)=><li key={i}>{tool}</li>)}</ul>
            </div>
          </div>
        ))}
      </div>
    </div>
    </div>
    </div>
  );
}

export default App;
