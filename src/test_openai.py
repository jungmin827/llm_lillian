import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
        {"role": "system", "content": "You are a helpful AI."},
        {"role": "user", "content": "Test message to check if API works!"}
  ]
)

print(response.choices[0].message.content)
