import React, { useState } from 'react'
import './App.css';

function App() {
  const [ingredientsInput, setIngredientsInput] = useState('')
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const ingredients = ingredientsInput
      .split(',')
      .map((i) => i.trim())
      .filter((i) => i)
    if(ingredients.length === 0) {
      setError("Please enter at least one ingredient")
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/find_recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ingredients, top_k: 5})
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
    <div className="App">
      <header><h1>Recipe Generator</h1></header>
      <header><h2>Enter the ingredients that you want to use to have recipe suggestions generated for you!</h2></header>
      <form onSubmit={handleSubmit} className="space-y-4">
        <label>
          Ingredients (comma-separated):
          <div class="recipe-search-bar">
          <input
            type="text"
            value={ingredientsInput}
            onChange={(e) => setIngredientsInput(e.target.value)}
            placeholder="e.g. mushrooms, tofu, garlic"
            className={`flex-1 px-4 py-2 border-2 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-2xl ${
              error ? 'border-red-300' : 'border-gray-300'
            }`}
          />
          </div>

        </label>
        <button type="submit" class="search-bar-button button" disabled={loading}>
          {loading ? 'Searching...' : 'Find Recipes'}
        </button>
      </form>

      {error && <div className='Error'>{error}</div>}

      <div className='Recipes'>
        {recipes.map((r, idx) => (
          <div key={idx} className="RecipeCard">
            <h2><a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a></h2>
            <p><em>Cook time:</em>{r.cook_time_mins} mins</p>
            <p>{r.summary}</p>
            <details>
              <summary>Ingredients</summary>
              <ul>{r.ingredients.map((ing,i)=><li key={i}>{ing}</li>)}</ul>
            </details>
            <details>
              <summary>Steps</summary>
              <ol>{r.steps.map((st,i)=><li key={i}>{st}</li>)}</ol>
            </details>
            </div>
        ))}
    </div>
    </div>
  );
}

export default App;
