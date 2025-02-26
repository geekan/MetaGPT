
## Roadmap

### Long-term Objective

Enable MetaGPT to self-evolve, accomplishing self-training, fine-tuning, optimization, utilization, and updates.

### Short-term Objective

1. Become the multi-agent framework with the highest ROI.
2. Support fully automatic implementation of medium-sized projects (around 2000 lines of code).
3. Implement most identified tasks, reaching version 1.0.

### Tasks

1. Usability
   1. ~~Release v0.01 pip package to try to solve issues like npm installation (though not necessarily successfully)~~ (v0.3.0)
   2. ~~Support for overall save and recovery of software companies~~ (v0.6.0)
   3. ~~Support human confirmation and modification during the process~~ (v0.3.0) New: Support human confirmation and modification with fewer constrainsts and a more user-friendly interface
   4. Support process caching: Consider carefully whether to add server caching mechanism
   5. ~~Resolve occasional failure to follow instruction under current prompts, causing code parsing errors, through stricter system prompts~~ (v0.4.0, with function call)
   6. Write documentation, describing the current features and usage at all levels (ongoing, continuously adding contents to [documentation site](https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html))
   7. ~~Support Docker~~
2. Features
   1. ~~Support a more standard and stable parser (need to analyze the format that the current LLM is better at)~~ (v0.5.0)
   2. ~~Establish a separate output queue, differentiated from the message queue~~ (v0.5.0)
   3. ~~Attempt to atomize all role work, but this may significantly increase token overhead~~ (v0.5.0)
   4. Complete the design and implementation of module breakdown
   5. Support various modes of memory: clearly distinguish between long-term and short-term memory
   6. Perfect the test role, and carry out necessary interactions with humans
   7. ~~Allowing natural communication between roles~~ (v0.5.0)
   8. Implement SkillManager and the process of incremental Skill learning (experimentation done with game agents)
   9. Automatically get RPM and configure it by calling the corresponding openai page, so that each key does not need to be manually configured
   10. ~~IMPORTANT: Support incremental development~~ (v0.5.0)
3. Strategies
   1. Support ReAct strategy (experimentation done with game agents)
   2. Support CoT strategy (experimentation done with game agents)
   3. ~~Support ToT strategy~~ (v0.6.0)
   4. Support Reflection strategy (experimentation done with game agents)
   5. ~~Support planning~~ (v0.7.0)
4. Actions
   1. ~~Implementation: Search~~ (v0.2.1)
   2. Implementation: Knowledge search, supporting 10+ data formats
   3. ~~Implementation: Data EDA~~ (v0.7.0)
   4. ~~Implementation: Review & Revise~~ (v0.7.0)
   5. ~~Implementation: Add Document~~ (v0.5.0)
   6. ~~Implementation: Delete Document~~ (v0.5.0)
   7. Implementation: Self-training
   8. ~~Implementation: DebugError~~ (v0.2.1)
   9. Implementation: Generate reliable unit tests based on YAPI
   10. Implementation: Self-evaluation
   11. Implementation: AI Invocation
   12. ~~Implementation: Learning and using third-party standard libraries~~ (v0.7.0)
   13. Implementation: Data collection
   14. Implementation: AI training
   15. ~~Implementation: Run code~~ (v0.2.1)
   16. ~~Implementation: Web access~~ (v0.2.1)
5. Tools
   1. ~~Support SERPER api~~
   2. ~~Support Selenium apis~~
   3. ~~Support Playwright apis~~
   4. Plugins: Compatibility with plugin system  
6. Roles
   1. Perfect the action pool/skill pool for each role
   2. E-commerce seller
   3. ~~Data analyst~~ (v0.7.0)
   4. News observer
   5. ~~Institutional researcher~~ (v0.2.1)
   6. User  
7. Evaluation
   1. Support an evaluation on a game dataset (experimentation done with game agents)
   2. Reproduce papers, implement full skill acquisition for a single game role, achieving SOTA results (experimentation done with game agents)
   3. Support an evaluation on a math dataset (expected v0.8.0)
   4. Reproduce papers, achieving SOTA results for current mathematical problem solving process (expected v0.8.0)
8. LLM
   1. ~~Support Claude underlying API~~
   2. ~~Support Azure asynchronous API~~
   3. ~~Support streaming version of all APIs~~
   4. ~~Make gpt-3.5-turbo available (HARD)~~
9. Other
   1. ~~Clean up existing unused code~~
   2. ~~Unify all code styles and establish contribution standards~~
   3. ~~Multi-language support~~
   4. ~~Multi-programming-language support~~