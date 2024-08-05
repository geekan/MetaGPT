#!/bin/bash

pip install flake8

# Default Mode from SWE-Bench
# https://github.com/princeton-nlp/SWE-agent/blob/ca54d5556b9db4f4f2be21f09530ce69a72c0305/config/configs/default_sys-env_window100-detailed_cmd_format-last_5_history-1_demos.yaml#L103-L106
SCRIPT_PATH="${BASH_SOURCE[0]}"  # use BASH_SOURCE to avoid the influence of `source *.sh which cause CUR_DIR=/bin`
CUR_DIR=$(dirname $(readlink -f $SCRIPT_PATH))
REPO_ROOT_DIR=$CUR_DIR"/../../.."
source $REPO_ROOT_DIR/metagpt/tools/swe_agent_commands/_setup_default_env.sh

# make _split_string (py) available
export PATH=$PATH:$REPO_ROOT_DIR/metagpt/tools/swe_agent_commands

source $REPO_ROOT_DIR/metagpt/tools/swe_agent_commands/defaults.sh
source $REPO_ROOT_DIR/metagpt/tools/swe_agent_commands/search.sh
source $REPO_ROOT_DIR/metagpt/tools/swe_agent_commands/edit_linting.sh

echo "SWE_CMD_WORK_DIR: $SWE_CMD_WORK_DIR"
