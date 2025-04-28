import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  jest.resetAllMocks()
})

test('renders search bar and search button', () => {
  render(<App />)
  expect(screen.getByPlaceholderText(
    /Enter recipe requirements, e\.g\. tofu, broccoli, vegetarian/i
  )).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: /Find Recipes/i })
  ).toBeInTheDocument()
})

test('shows error if search button pressed when search bar is empty', async () => {
  render(<App />)
  fireEvent.click(screen.getByRole('button', { name: /Find Recipes/i }))
  expect(
    await screen.findByText(/Please enter at least one recipe requirement\/ingredient/i)
  ).toBeInTheDocument()
})

test('disables input and button shows "Searching..." on submit', async () => {
  globalThis.fetch = jest.fn(() => new Promise(() => {}))
  render(<App />)
  const input = screen.getByPlaceholderText(/Enter recipe requirements, e\.g\. tofu, broccoli, vegetarian/i)
  const button = screen.getByRole('button', { name: /Find Recipes/i })

  fireEvent.change(input, { target: {value: 'mushrooms'}})
  fireEvent.click(button)

  expect(input).toBeDisabled()
  expect(button).toBeDisabled()
  expect(screen.getByText(/Searching\.\.\./i)).toBeInTheDocument()
})

test('renders recipe cards on successful fetch', async () => {
  const mockRecipe = {
    title: "Creamy Mushroom Pasta",
    url: "http:creamymushroompasta.com",
    cook_time_mins: 35,
    ingredients: ["pasta", "mushrooms", "cream", "parmesan", "lemon"],
    steps: [
      "Cook pasta",
      "Chop mushrooms",
      "Cook mushrooms",
      "Add cream and pasta water",
      "Add in pasta",
      "Let reduce",
      "Add lemon zest, salt, and pepper to taste",
    ],
    tools: ["pot", "pan", "zester"],
    source_url: "http:creamymushroompasta.com"
  }

  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ results: [mockRecipe] })
    })
  )

  render(<App />)
  const input = screen.getByPlaceholderText(/Enter recipe requirements, e\.g\. tofu, broccoli, vegetarian/i)
  fireEvent.change(input, { target: { value: 'mushrooms' }})
  fireEvent.click(screen.getByRole('button', {name: /Find Recipes/i}))

  expect(await screen.findByText("Creamy Mushroom Pasta")).toBeInTheDocument()
  expect(screen.getByText(/Cook time: 35 mins/i)).toBeInTheDocument()
  expect(screen.getByText("mushrooms")).toBeInTheDocument()
})

test("display server error on failed fetch", async () => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: false,
      text: () => Promise.resolve("Server error occured")
    })
  )

  render(<App />)
  const input = screen.getByPlaceholderText(/Enter recipe requirements, e\.g\. tofu, broccoli, vegetarian/i)
  fireEvent.change(input, { target: { value: 'tofu' }})
  fireEvent.click(screen.getByRole('button', {name: /Find Recipes/i}))

  expect(await screen.findByText(/Server error occured/i)).toBeInTheDocument
})
