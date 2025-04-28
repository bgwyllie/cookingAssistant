# AI Cooking Assistant

An AI-powered cooking assistant that provides the user recipes based on the inputted ingredients that they have in their home kitchen or fridge (i.e. , a green pepper, some rice, some cooked chicken, etc.).
The assistant will provide them with a recipe using these input ingredients, including cooking instructions and tools they will need, estimated cook time, as well as a source reference for the recipe.

### Notes

I initially developed the app so that the user would have to input a comma separated list of ingredients but that wasn't the best user experience. As well, I have dietary restrictions so I wanted that to be included in the search. So instead of having to input a comma separated list, the user can input whatever they want related to their recipe requirements.
E.g.
"high-protein vegetarian spinach artichoke", 
"blueberry gluten-free baking",
"mushrooms, pasta, lemon, parmesan"

I used OpenAI's GPT-4.1-mini model for the development due to its high performance and resonably low latency. It could be changed to GPT-4.1-nano or GPT-o4-mini depending on the perfomance requirements. As it stands, this works well for the beta app. However, latency is currently still an issue, there is a bottleneck but so far I have not been able to locate it. Each microservice runs quickly so I would have to do further testing to locate the issue. As well, this is a beta version so there are still kinks to be worked out.

I currently have it set so that only the top 3 recipes are shown, as to not overwhelm the user but this could easily be scaled to show the user more recipe options.

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
docker-compose up --build

How to run the integration tests
pytest tests/integration

Each microservice has tests
Enter the folder and run pytest -q

## React Web App

The web app is a single page web app created using React.
To run the app:
cd client
npm start

To test the UX/UI
npm test

## Microservices

### Orchestration Service

TLDR; This is the service that the frontend communicates with, it ties all the other services into one. It receives user input and outputs the top_k recipes.

This service takes in a string of ingredients and the value of top_k (currently a constant set to 3). It then goes through each of the microservices in sequence. First, it does a POST call to the /generate_queries endpoint from the query_planner to get a small list of concise web-search prompts. Next, it does a POST call to /search_urls endpoint from the search_service to get a list of recipe URLs based on the web-search prompts. With the list of URLs, it does a POST call to the /fetch_html endpoint in the html_fetcher service that returns cleaned HTML (without script and style tags). Now that the HTML is cleaned, it makes a POST call to the /extract_recipe endpoint that extracts the required recipe information. The recipes are then sent to the ranker service and a POST call is made to the /rank_recipes endpoint to order the recipes by the best match based on the user requirements. Finally, the orchestration service gets the top_k recipes from the ranker service and sends the structed recipes to the frontend to be displayed.

### Query Planner Service

TLDR; Makes a POST request to OpenAI to transform the user input into search queries

This service takes in a string from the frontend which can be any recipe criteria from the user. Using a POST request (/generate_queries), it sends the string to OpenAI's Response API (GPT-4.1-mini) and based on the input string, it builds 3 concise search prompts to be used to find recipes for the user requirements.
The model returns an the search prompts. The array is accessed and split at each new line break. The query_planner returns a List of strings with the queries to be used in the search.
Ex.
User input: "mushroom cream"
Generated queries:

```
"queries": [
    "mushroom cream sauce recipes",
    "creamy mushroom pasta recipes",
    "easy mushroom cream soup recipe"
]
```

### Search Service

TLDR; Makes a POST request to OpenAI and uses the generated of queries to gather a list of real recipe links

This service takes in the generated queries from the query_planner service and a value of num_results which is the maximum returned results. Using a POST request (/search_urls), it loops through each query in the queries list and leverages OpenAI's web_search_preview tool (GPT-4.1-mini) to find recipes related to the search terms.
The model returns the recipe title and url. The response is converted to a dictionary and the results array is extracted from the dictionary. If there isn't a results array, there is an alternate way to get the URL and title through annotation.type.

To ensure that no duplicate recipes are shown, we have a seen_recipes set to keep tract or the recipes that need to be discarded. If it has not been seen, then it gets added to results, otherwise it is added to seen_recipes. This stops once the length of results has reached num_results and then the deduplicated list of recipe urls and titles are returned.

### HTML Fetcher Service

TLDR; Makes a POST request to OpenAI to retrieve and sanitize raw HTML based on the list of URLs from Search Service.

This service takes in a the list of URLs that the Search Service found based on the user requirements. It makes a POST request (/fetch_html) to OpenAI's Response API (GPT-4.1-mini) for each URL. It loops through the URLs and it downloads the page then feeds it into BeautifulSoup where the information is scraped from the web page and then the `<script>` and `<style>` tags are removed. The cleaned HTML is returned as a string. The html_fetcher service then returns a JSON array of cleaned HTML with its URL.
Ex.

```
input:
{
  "urls": [
    "http://creamymushroompasta.com",
    "http://mushroomrisotto.com"
  ]
}

output:
{
  "results": [
    {
      "url": "http://creamymushroompasta.com",
      "html": "<html><body>…only the page content…</body></html>"
    },
    {
      "url": "http://mushroomrisotto.com",
      "html": "<html><body>…only the page content…</body></html>"
    }
  ]
}
```

### Extractor Service

TLDR; Makes a POST request to OpenAI to transform a recipe's HTML into a structured recipe JSON object

This service takes in a JSON with the recipe page's url and the raw HTML. Using a POST request (/extract_recipe), it sends the HTML to OpenAI's Response API (GPT-4.1-mini) telling it that it is a recipe extractor and here is the HTML for the recipe page. The request asks for it to return a JSON object that exactly matches this schema:

```
recipe_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "ingredients": {"type": "array", "items": {"type": "string"}},
        "steps": {"type": "array", "items": {"type": "string"}},
        "tools": {"type": "array", "items": {"type": "string"}},
        "cook_time_mins": {"type": "integer"},
        "source_url": {"type": "string"},
    },
    "required": [
        "title",
        "ingredients",
        "steps",
        "tools",
        "cook_time_mins",
        "source_url",
    ],
    "additionalProperties": False,
}
```

The recipe schema tells the API that the title, ingredients, steps, tools, cook time (minutes), and the url are required. It also tells it what format to return each in and not to return any extra fields.
The returned response is a blob of text which is then parsed into a Python dictionary using json.loads() and the \*\* operator unpacks dictionary into keyword arguments. The returned as a structured JSON response

### Ranker Service

TLDR; Using the recipe requirements and the candidate recipe list, uses a LLM to pick the top k recipes.

This service takes in the user requirements, the list of recipes and the top_k is set in this case to 3. With the information from the user requirements and each recipe's metadata, this service converts them into a prompt for the LLM. It makes a POST request (/rank_recipes) to OpenAI's Response API (GPT-4.1-mini) with a rank_schema, asking the model to return a JSON object with the ranked IDs of the recipes.
The response of the model is read, parsed and converted to a Python dictionary. From the dictionary, the ranked_ids are accessed, then the original recipe list is reorded with that order. It takes only the top_k of the list and returns that list of recipes.
