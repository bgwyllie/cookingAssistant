# AI Cooking Assistant

An AI-powered cooking assistant that provides the user recipes based on the inputted ingredients that they have in their home kitchen or fridge (i.e. , a green pepper, some rice, some cooked chicken, etc.).
The assistant will provide them with a recipe using these input ingredients, including cooking instructions and tools they will need, estimated cook time, as well as a source reference for the recipe.

## Getting Started

1. Clone this repository
2. Create and activate the Python Virtual Environment

```
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```
pip install -e
pre-commit install
```

How to run all the services locally
cd infra
docker-compose up --build

How to run the integration tests
pytest tests/integration
