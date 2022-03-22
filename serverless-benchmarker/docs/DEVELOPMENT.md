# Development

Describes the development setup, implementation insights, challenges, etc.

## Install dependencies

```sh
make install
```

## Linting

```sh
make lint
```

## Tests

```sh
make test
# Selectively run unit or integration tests
make unit_test
make integration_test
```

## VSCode

* Example settings: [settings.sample.json](../.vscode/settings.sample.json). Change `python.pythonPath`
* Recommended plugins: [extensions.json](../.vscode/extensions.json)
* [Python testing in VSCode](https://code.visualstudio.com/docs/python/testing)

## Debugging

* Use the tests and local mode to debug
* Alternatively, an interactive Python shell can be used as breakpoint by inserting the following snippet into the code:

  ```py
  # Native
  import code; code.interact(local=dict(globals(), **locals()))
  # With ipdb (requires dev dependencies or pip install ipdb)
  import ipdb; ipdb.set_trace()
  ```
