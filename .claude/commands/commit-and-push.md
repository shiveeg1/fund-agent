Commit all current changes and push them to the active branch. The commit message is "$ARGUMENTS".

Steps:
1. Run `git status` to confirm there are changes to commit. If the working tree is clean, tell the user and stop.
2. Run `git diff --staged && git diff` to review staged and unstaged changes.
3. Stage all changed files with `git add -A`.
4. Commit with the message provided: `git commit -m "$ARGUMENTS"`.
5. Determine the current branch with `git branch --show-current`.
6. Push to the remote: `git push -u origin <current-branch>`.
7. Confirm to the user that the commit and push succeeded, including the branch name and commit hash.
