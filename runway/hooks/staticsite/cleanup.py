"""Replicated Function Remover."""
import logging
import json
from typing import Any, Dict, Optional, Union  # pylint: disable=unused-import

from runway.cfngin.context import Context  # pylint: disable=unused-import
from runway.cfngin.providers.base import BaseProvider  # pylint: disable=unused-import
from runway.cfngin.session_cache import get_session

LOGGER = logging.getLogger(__name__)


def execute(context,  # type: Context # pylint: disable=unused-argument
            provider,  # type: BaseProvider
            **kwargs  # type: Optional[Dict[str, Any]]
           ):  # noqa: E124
    # type: (...) -> Union[Dict[str, Any], bool]
    """Execute the cleanup process.

    A StateMachine will be executed that stays active after the main and
    dependency stacks have been deleted. This will keep attempting to
    delete the Replicated functions that were created as part of the main
    stack. Once it has deleted all the Lambdas supplied it will self
    destruct its own stack.

    Args:
        context (:class:`runway.cfngin.context.Context`): The context
            instance.
        provider (:class:`runway.cfngin.providers.base.BaseProvider`):
            The provider instance

    Keyword Args:
        function_arns (List[str]): The arns of all the Replicated functions to
            delete
        state_machine_arn (str): The ARN of the State Machine to execute
        stack_name (str): The name of the Cleanup stack to delete
    """
    session = get_session(provider.region)
    step_functions_client = session.client('stepfunctions')

    try:
        step_functions_client.start_execution(
            stateMachineArn=kwargs['state_machine_arn'],
            input=json.dumps({
                "SelfDestruct": {
                    "StateMachineArn": kwargs['state_machine_arn'],
                    "StackName": kwargs['stack_name'],
                },
                "FunctionArns": kwargs['function_arns']
            })
        )
        return True
    except Exception as err:  # pylint: disable=broad-except
        LOGGER.error('Could not execute cleanup process.')
        LOGGER.error(err)
        return False
