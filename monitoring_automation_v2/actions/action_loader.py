class ActionLoader:

    def __init__(self):
        self._actions = {}

    def register_action(self, code, action):
        self._actions[code] = action

    def get_action_handler(self, active_action, elk_key, request, **kwargs):
        action = self._actions.get(active_action, None)
        if not action:
            raise ValueError(active_action)
        return action(elk_key, request, **kwargs)