
## Roadmap

### Long-term Objective

Enable MetaGPT to self-evolve, accomplishing self-training, fine-tuning, optimization, utilization, and updates.

### Short-term Objective

1. Become the multi-agent framework with the highest ROI.
2. Support fully automatic implementation of medium-sized projects (around 2000 lines of code).
3. Implement most identified tasks, reaching version 0.5.

### Tasks

To reach version v0.5, approximately 70% of the following tasks need to be completed.

1. Usability
   1. Release v0.01 pip package to try to solve issues like npm installation (though not necessarily successfully)
   2. Support for overall save and recovery of software companies
   3. Support human confirmation and modification during the process
   4. Support process caching: Consider carefully whether to add server caching mechanism
   5. Resolve occasional failure to follow instruction under current prompts, causing code parsing errors, through stricter system prompts
   6. Write documentation, describing the current features and usage at all levels
   7. ~~Support Docker~~
2. Features
   1. Support a more standard and stable parser (need to analyze the format that the current LLM is better at)
   2. ~~Establish a separate output queue, differentiated from the message queue~~
   3. Attempt to atomize all role work, but this may significantly increase token overhead
   4. Complete the design and implementation of module breakdown
   5. Support various modes of memory: clearly distinguish between long-term and short-term memory
   6. Perfect the test role, and carry out necessary interactions with humans
   7. Provide full mode instead of the current fast mode, allowing natural communication between roles
   8. Implement SkillManager and the process of incremental Skill learning
   9. Automatically get RPM and configure it by calling the corresponding openai page, so that each key does not need to be manually configured
3. Strategies
   1. Support ReAct strategy
   2. Support CoT strategy
   3. Support ToT strategy
   4. Support Reflection strategy
4. Actions
   1. Implementation: Search
   2. Implementation: Knowledge search, supporting 10+ data formats
   3. Implementation: Data EDA
   4. Implementation: Review
   5. Implementation: Add Document
   6. Implementation: Delete Document
   7. Implementation: Self-training
   8. Implementation: DebugError
   9. Implementation: Generate reliable unit tests based on YAPI
   10. Implementation: Self-evaluation
   11. Implementation: AI Invocation
   12. Implementation: Learning and using third-party standard libraries
   13. Implementation: Data collection
   14. Implementation: AI training
   15. Implementation: Run code
   16. Implementation: Web access
5. Plugins: Compatibility with plugin system
6. Tools
   1. ~~Support SERPER api~~
   2. ~~Support Selenium apis~~
   3. ~~Support Playwright apis~~
7. Roles
   1. Perfect the action pool/skill pool for each role
   2. Red Book blogger
   3. E-commerce seller
   4. Data analyst
   5. News observer
   6. Institutional researcher
8. Evaluation
   1. Support an evaluation on a game dataset
   2. Reproduce papers, implement full skill acquisition for a single game role, achieving SOTA results
   3. Support an evaluation on a math dataset
   4. Reproduce papers, achieving SOTA results for current mathematical problem solving process
9. LLM
   1. Support Claude underlying API
   2. ~~Support Azure asynchronous API~~
   3. Support streaming version of all APIs
   4. ~~Make gpt-3.5-turbo available (HARD)~~
10. Other
    1. Clean up existing unused code
    2. Unify all code styles and establish contribution standards
    3. Multi-language support
    4. Multi-programming-language support
