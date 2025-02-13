PROMPT_OPTIMIZE_PROMPT = """
You are building a prompt to address user requirement. Based on the given prompt, 
please reconstruct and optimize it. You can add, modify, or delete prompts. Please include a single modification in 
XML tags in your reply. During the optimization, you can incorporate any thinking models.
This is a prompt that performed excellently in a previous iteration. You must make further optimizations and improvements based on this prompt. The modified prompt must differ from the provided example.

requirements:
```
{requirements}
```

reference prompt:
```
{prompt}
```

The execution result of this reference prompt is(some cases):
```
{answers}
```

The best answer we expect(some cases):
```
{golden_answers}
```

Provide your analysis, optimization points, and the complete optimized prompt using the following XML format:

<analyse>Analyze what drawbacks exist in the results produced by the reference prompt and how to improve them.</analyse>
<modification>Summarize the key points for improvement in one sentence</modification>
<prompt>Provide the complete optimized prompt {count}</prompt>
"""
