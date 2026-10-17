# HackHarvard 2026 Team Project

Working repository name: `hackharvard-clinical-trials`.

This is our shared workspace for HackHarvard 2026. Clinical trials are the current idea. The team has not yet chosen the project scope or tech stack. Update this README as needed.

## Getting started

1. Accept your GitHub repository invitation.
2. Clone this repository using its green **Code** button, then open the folder in your editor.
3. Add setup and run instructions here once the team chooses its tools.

## Working together

Keep `main` ready for the demo. Use a short branch for each task:

```sh
git switch main
git pull --ff-only
git switch -c your-name/short-task
# Make your changes, then stage only the files you intend to share:
git add path/to/file
git commit -m "Describe what changed"
git push -u origin your-name/short-task
```

On GitHub, open a pull request into `main`. Explain what changed and how you checked it, then ask a teammate to review before merging. After merging, switch back to `main` and pull before starting your next task. GitHub's web editor is also fine for small documentation edits; choose a new branch and open a pull request.

Keep tasks small. Use GitHub Issues if the team prefers them; link the issue in your pull request.

## Repository access

The owner can invite teammates from **Settings → Collaborators → Add people**, using each person's GitHub handle. Teammates must accept the invitation. Start private and revisit visibility together before sharing the demo or submission.

## Data and secrets

Do not commit API keys, passwords, `.env` files, or personal/participant health data. Use synthetic or appropriately public demo data. If configuration becomes necessary, add an `.env.example` containing placeholders only. Ignored files are not a substitute for checking what you commit.

## Demo and submission

Add the demo link, screenshots, team members, data sources, and any required attribution here when available.
