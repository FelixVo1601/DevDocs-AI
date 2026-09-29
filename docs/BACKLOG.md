# Post-MVP backlog

**Not in MVP v1.** MVP v1 is frozen. These are ideas for a later phase, not a commitment to build them and not a design. Nothing here is in the current product scope. The scope contract stays [MVP.md](MVP.md).

## Ideas

- **Async index jobs.** Today `POST /github/selected-repo/index` runs fetch, chunk, and embed in the request. A later version could queue that work and poll status.
- **More than one repository.** Today each user has one selected repository. A later version could keep several indexes and choose which one a question uses.
- **Agents.** Multi-step loops that plan, search again, or call tools. MVP answers are one retrieve-then-answer pass.
- **Writing code.** Edits, commits, or generated pull requests. MVP is read-only.
- **More than one model provider.** MVP uses one OpenAI-compatible base URL, embedding model, and chat model from env.
- **Teams.** Shared workspaces, roles, or a repo indexed once for many users.
- **Product extras already deferred.** Usage analytics, billing, a mobile app, and Kubernetes deployment.

Demo of what v1 does include: log in, connect GitHub, select a repository, index it, ask, read citations, open the cited source. Steps: [SMOKE.md](SMOKE.md).
