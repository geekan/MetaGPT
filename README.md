# Minion README

## Features

Minion is designed to execute and analyze complex queries, offering a variety of features that demonstrate its flexibility and intelligence.

## Minion Design

The core logic of Minion is implemented in `examples/smart_minion/brain.py`. You can experiment with different examples by modifying the code, as various scenarios are commented out for easy testing.

### Example Usage

```python
obs, score, *_ = await brain.step(query="what's the solution for game of 24 for 4 3 9 8")
print(obs)

obs, score, *_ = await brain.step(query="what's the solution for game of 24 for 2 5 11 8")
print(obs)

obs, score, *_ = await brain.step(query="solve x=1/(1-beta^2*x) where beta=0.85")
print(obs)

obs, score, *_ = await brain.step(
    query="Write a 50000 characters novel named 'Reborn in Skyrim'. "
          "Fill the empty nodes with your own ideas. Be creative! Use your own words!"
          "I will tip you $100,000 if you write a good novel."
          "Since the novel is very long, you may need to divide it into subtasks."
)
print(obs)
```
## Get Started

### Installation

Minion current depends on metagpt to call llm and response format parsing, please follow metagpt's installation
guide of [setup metagpt](https://github.com/geekan/MetaGPT#get-started), basically it's
```
pip install --upgrade metagpt
metagpt --init-config # this will create ~/.metagpt/config2.yaml
```
then edit ~/.metagpt/config2.yaml
```
llm:
  api_type: "openai"  # or azure / ollama / groq etc. Check LLMType for more options
  model: "gpt-4-turbo"  # or gpt-3.5-turbo
  base_url: "https://api.openai.com/v1"  # or forward url / other llm url
  api_key: "YOUR_API_KEY"
```

### Other Dependencies
#### install minion
```
git clone https://github.com/femto/MetaGPT.git && cd MetaGPT && pip install -r requirements.txt
```
#### install intercode(which minion depends as virtual env to execute code)
```
git clone https://github.com/princeton-nlp/intercode
cd intercode
docker build -t intercode-python -f docker/python.Dockerfile .  
```
make sure container name intercode-python_ic_ctr is listenning on 3006,  
the code in PythonEnv(from intercode) tries to automatically start intercode-python_ic_ctr,
the PythonEnv seem can start the container, but can't map port. So if you can't connect
to intercode-python_ic_ctr, stop the container and start it the following way:
```
docker run -d -p 3006:3006 --name intercode-python_ic_ctr intercode-python
```

## Enjoy Your Brain.Step() Journey

Then enjoy you brain.step("some requirement") journey
currently game of 24 and solve equation can reach near 100% accuracy,
while writing novel can generate plan, I'm still writing what's left.

