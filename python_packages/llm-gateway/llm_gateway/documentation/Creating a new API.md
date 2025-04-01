### Instructions on adding a new API to `/models/`

1. Create your [API].py file within the correct `/models/` directory _(see `Adding a new type.md` on how to create one of those..)_.

2. Add the model name to its respective enum in `/models/[model type]/core/interfaces.py`.

3. Add the new required variable(s) to `.env.example`.

4. Add a new case to `/models/providers.py`.

5. Create a test in the respective `/tests/test_*.py`. **Create a `/tests/.env` and add the necessary enviromental variables for the provider in order to run it!** You can run tests using `pytest` but the VSC Testing tab is much more practical _if available_.

6. Have fun tweaking and testing your new API addition!
