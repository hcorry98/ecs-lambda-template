from awsLambda.presenters.EcsPresenter import EcsPresenter
from awsLambda.views.Handle import Handle

class RunEcsTask(Handle):
    """The view for running an ECS task.

    This extends the Handle class and overrides the _run method to call the presenter for running an ECS task.
    This implements the Template Method pattern.
    """

    def __init__(self, *args) -> None:
        """Initializes the RunEcsTask through the Handle's constructor."""
        super(RunEcsTask, self).__init__(*args)

    def _run(self) -> tuple[int, dict]:
        """Runs the ECS task presenter.

        This method overrides the Handle's _run method and calls the presenter for running an ECS task.
        This completes the Template Method pattern.

        Returns:
            tuple[int, dict]: 
                int: the status code
                dict: response from running the Handle
        """
        ecsPresenter = EcsPresenter(self.event, self.test)
        return ecsPresenter.run()
