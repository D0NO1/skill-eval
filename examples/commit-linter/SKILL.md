---
name: commit-linter
description: Demo skill — write commit messages that follow Conventional Commits. Used to demonstrate the skill-eval harness.
---

# Commit Linter (demo skill)

When asked to write a commit message for a diff:

1. Read the diff file provided in the workspace.
2. Write a commit message to `commit-msg.txt`.
3. The subject line MUST follow Conventional Commits:
   `type(scope)?: description` where type is one of
   `feat|fix|docs|refactor|test|chore`.
4. When the change has non-obvious motivation, add a body explaining WHY.
