## MetaGPT Usage

### Configuration

- Configure your `key` in any of `~/.metagpt/config2.yaml / config/config2.yaml`
- Priority order: `~/.metagpt/config2.yaml > config/config2.yaml`

```bash
# Copy the configuration file and make the necessary modifications.
cp config/config2.yaml ~/.metagpt/config2.yaml
```

### Initiating a startup

```shell
# Run the script
metagpt "Write a cli snake game"
# Do not hire an engineer to implement the project
metagpt "Write a cli snake game" --no-implement
# Hire an engineer and perform code reviews
metagpt "Write a cli snake game" --code_review
```

After running the script, you can find your new project in the `workspace/` directory.

### Preference of Platform or Tool

You can tell which platform or tool you want to use when stating your requirements.

```shell
metagpt "Write a cli snake game based on pygame"
```

### Usage

```
NAME
    metagpt - We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.

SYNOPSIS
    metagpt IDEA <flags>

DESCRIPTION
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.

POSITIONAL ARGUMENTS
    IDEA
        Type: str
        Your innovative idea, such as "Creating a snake game."

FLAGS
    --investment=INVESTMENT
        Type: float
        Default: 3.0
        As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    --n_round=N_ROUND
        Type: int
        Default: 5

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```