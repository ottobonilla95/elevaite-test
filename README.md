# iOPEX elevAIte Suite Monorepo

## Structure

This repository utilizes [Turborepo](https://turbo.build/repo/docs) on NodeJS for JavaScript/TypeScript applications and packages and [uv](https://docs.astral.sh/uv/) for Python APIs and middleware programs.

### Turborepo Setup

The JavaScript/TypeScript portion of the repository is structured in an [npm workspace](https://docs.npmjs.com/cli/v7/using-npm/workspaces) like this:

    |> package.json
    |> turbo.json
    |> apps
    |  |> {...javascript applications}
    |> packages
    |  |> {...javascript packages}
    |> ...

The `package.json` file defines the workspace as well as dependencies required for the build system.
The `turbo.json` file defines the turborepo setup, some common tasks and their dependencies, as well as environmental variables to be use in the applications.
The `apps` directory contains all (at the moment [Next.JS](https://nextjs.org/)) applications.
The `packages` directory contains the internal packages to be used in the applications, like configurations and common ui components.
**The `.env` file contains enviromental variables for all the apps, please don't forget to add placeholders here when creating new variables for the frontend.**

### Python Setup

Python programs and packages are (mostly) co-located in the `elevaite_backend` directory

## Branch Strategy

**This repository follows a modified Git Flow branch strategy.**

### What is Git Flow

Git Flow was [introduced in 2010 by Vincent Driessen in their blog](https://nvie.com/posts/a-successful-git-branching-model/). Please read the blogpost for further clarification.
![Git Flow Diagram](https://nvie.com/img/git-model@2x.png)

### Modifications

- `master` branch renamed to `main`, to match Github's rules
- Prefer linear history as it has a more manageable tree
- For the time being we are not tagging releases
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) preferred

> Written with [StackEdit](https://stackedit.io/).
