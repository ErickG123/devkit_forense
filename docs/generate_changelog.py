import subprocess
from pathlib import Path

def get_changelog():
    tags = subprocess.check_output(['git', 'tag', '--sort=-creatordate']).decode().split()
    changelog_dir = Path("docs/changelog")
    changelog_dir.mkdir(parents=True, exist_ok=True)

    changelog = "# Changelog\n\n"

    if not tags:
        commits = subprocess.check_output(['git', 'log', '--pretty=format:* %s']).decode()
        changelog += f"## Unreleased\n{commits}\n\n"

        with open("CHANGELOG.md", "w", encoding="utf-8") as f:
            f.write(changelog)

        with open(changelog_dir / "unreleased.md", "w", encoding="utf-8") as f:
            f.write(f"# Unreleased\n\n{commits}\n")

        return

    for i, tag in enumerate(tags):
        if i + 1 < len(tags):
            previous_tag = tags[i + 1]
            commits = subprocess.check_output(
                ['git', 'log', f'{previous_tag}..{tag}', '--pretty=format:* %s']
            ).decode()
        else:
            commits = subprocess.check_output(
                ['git', 'log', f'{tag}', '--pretty=format:* %s']
            ).decode()

        changelog += f"## {tag}\n{commits}\n\n"

        with open(changelog_dir / f"{tag}.md", "w", encoding="utf-8") as f:
            f.write(f"# {tag}\n\n{commits}\n")

    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)

if __name__ == "__main__":
    get_changelog()
