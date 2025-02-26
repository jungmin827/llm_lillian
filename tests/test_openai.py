import openai
import config

openai.api_key = OPENAI_API_KEY

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": "You are a helpful AI."},
              {"role": "user", "content": "Test message to check if API works!"}]
)

print(response["choices"][0]["message"]["content"])
