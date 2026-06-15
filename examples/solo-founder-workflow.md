# Solo Founder Workflow

This example shows how a solo founder can use Discord and AI coding agents to organize software development work.

## Use case

A solo founder wants to build and maintain a small software project without a full engineering team.

The founder uses Discord as a command center for:

- capturing product ideas
- assigning coding tasks to Codex
- reviewing documentation updates
- tracking issues
- preparing release notes

## Suggested Discord channels

- #ideas
- #coding-tasks
- #codex-review
- #documentation
- #release-notes

## Workflow

1. Write a short task request in Discord.
2. Convert the request into a Codex task using `templates/codex-task-request.md`.
3. Ask Codex to inspect the relevant files.
4. Review the output manually.
5. Commit only small, understandable changes.
6. Update documentation or release notes when needed.

## Example task

“Update the README so new users can understand the project in less than five minutes.”

## Review rule

AI-generated output should not be accepted automatically.

The maintainer should review the result for:

- correctness
- clarity
- security
- unnecessary complexity
- usefulness for future contributors
