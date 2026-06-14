"""One-off script: fix garbled/boilerplate descriptions across resources.

Fixes:
- 22 files with cover-page boilerplate ("Printed in the United States...")
- 4 case files with garbled no-space descriptions
- Steiert: wrong title, wrong author, bad description
- Unreasonable Sufficiency: wrong author (listed as "Summer of Protocols")
- Deletes steiert-1 duplicate
"""

import re
import os
import json

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "../src/content/resources")

# Each entry can have: description, title, authors (list of {name, url?})
FIXES = {
    # --- Cover-page boilerplate replacements (description only) ---
    "2023-retrospectus.md": {
        "description": "The Summer of Protocols 2023 retrospective anthology — a collected volume of research papers, essays, and creative works from the inaugural year of the program.",
    },
    "a-phenomenology-of-protocols.md": {
        "description": "A phenomenological examination of protocols by Janna Tay — exploring how the rules and standards that govern coordination shape lived experience, perception, and the texture of everyday life.",
    },
    "addressable-space-pdf.md": {
        "description": "Chenoe Hart explores how protocols create addressable, navigable space — examining the relationship between spatial organization, naming systems, and the infrastructure that makes locations findable and reachable.",
    },
    "artificial-memory-and-orienting-infinity-pdf.md": {
        "description": "Kei Kreutler investigates artificial memory systems and the protocols that orient knowledge across vast scales — exploring how human and computational memory might be structured to navigate infinite information landscapes.",
    },
    "atoms-institutes-blockchains.md": {
        "description": "Josh Stark compares three fundamental coordination mechanisms — physical materials, legal institutions, and blockchains — as distinct protocol systems with different guarantees, failure modes, and affordances.",
    },
    "capital-enclosure-for-software-commons.md": {
        "description": "Trent Van Epps examines how capital and enclosure dynamics shape software commons, drawing on the histories of Linux and Ethereum to analyze tensions between open protocol ecosystems and commercial capture.",
    },
    "control-and-consciousness-of-time.md": {
        "description": "Saffron Huang explores how protocols shape our experience and control of time — examining the relationship between temporal coordination mechanisms, human consciousness, and the social structures that govern when and how we act.",
    },
    "dangerous-protocols.md": {
        "description": "Nadia Asparouhova examines the dark potential of protocols — how coordination systems can be captured, weaponized, or designed in ways that cause harm, and what makes certain protocols dangerous.",
    },
    "dangerous-dating-protocols.md": {
        "description": "Shreeda Segan explores romantic and social matching through the lens of protocol — how dating apps, courtship rituals, and social scripts function as coordination protocols with unintended consequences for connection and community.",
    },
    "dispatches-from-cascadia.md": {
        "description": "Rithikha Rajamohan's field dispatches from the Pacific Northwest explore regional governance and ecological protocols — examining how place, community, and environment shape the protocols people create to live together.",
    },
    "exit-to-protocol.md": {
        "description": "Shuya Gong examines exit rights and protocol design — exploring how individuals and communities can exercise meaningful exit from coordination systems, and what protocols must look like to enable genuine choice and voice.",
    },
    "good-death-pdf.md": {
        "description": "Sarah Friend investigates the protocols of dying — how end-of-life is structured by medical, legal, social, and cultural coordination systems, and what a 'good death' might require from the protocols that govern it.",
    },
    "protocol-pattern-language-anthology.md": {
        "description": "Drew Austin applies the pattern language concept to protocol design — collecting recurring structural patterns, anti-patterns, and design templates for building effective coordination systems across urban and digital spaces.",
    },
    "retrofitting-the-web-pdf.md": {
        "description": "Dorian Taylor examines how the web's foundational protocols might be retrofitted to address contemporary challenges — exploring the tension between backward compatibility and the need for meaningful reform of internet infrastructure.",
    },
    "safe-new-world-pdf.md": {
        "description": "Timber Stinson-Schroff explores safety as a protocol domain — examining how coordination systems govern risk, precaution, and harm prevention across technical, industrial, and social contexts.",
    },
    "summer-of-protocols-research-lang.md": {
        "description": "A Summer of Protocols 2023 research paper by David Lang exploring protocol systems in the context of standards, measurement, and collaborative making.",
    },
    "the-death-and-the-death-of-orkut.md": {
        "description": "Alice Noujaim analyzes Orkut's rise and fall as a case study in social network protocol death — examining what happens when coordination platforms lose critical mass, and what digital communities leave behind when they collapse.",
    },
    "the-fundamentals-of-protocol-systems.md": {
        "description": "Angela Walch provides a foundational analysis of how protocol systems are structured, maintained, and governed — with particular attention to power dynamics, accountability gaps, and the fiction of protocol neutrality.",
    },
    "the-swarm-effect-chinas-2022-covid-protests.md": {
        "description": "An anonymous analysis of China's 2022 Covid protests through the lens of swarm coordination — examining how leaderless, protocol-driven collective action enabled one of the country's largest waves of public dissent.",
    },
    "the-unreasonable-sufficiency-of-protocols.md": {
        "authors": [{"name": "Josh Stark"}, {"name": "Trent Van Epps"}, {"name": "Bastian Aue"}],
        "description": "Josh Stark, Trent Van Epps, and Bastian Aue argue that protocols are a surprisingly sufficient foundation for coordination at scale — making the case that apparent protocol simplicity belies transformative power across social, technical, and institutional domains.",
    },
    "weaving-memory.md": {
        "description": "Spencer Chang explores memory as protocol — examining how communities weave collective memory through practices, artifacts, and coordination systems, and what it means to design protocols that preserve and transmit what matters.",
    },
    # --- Steiert: title, author, and description ---
    "summer-of-protocols-research-steiert.md": {
        "title": "Protocols in (Emergency) Time",
        "authors": [{"name": "Olivia Steiert"}],
        "description": "Olivia Steiert explores how emergency conditions — from natural disasters to public health crises — reshape and reveal the underlying protocols that govern response, coordination, and collective care under pressure.",
    },
    # --- Case files: garbled no-space descriptions ---
    "fire-protocols-case-file.md": {
        "description": "After a century of fire suppression and heating atmospheric conditions, California has changed from a fire-ecology to a fire-climate. A case file exploring how our renewed ability to work with fire is reshaping environmental knowledge and protocol.",
    },
    "end-to-end-encryption-in-activitypub-case-file.md": {
        "description": "Every protocol deserves a second chance. ActivityPub (2018) is the distributed social network protocol, developed before end-to-end encryption (E2EE) was standard practice. A case file exploring how to bring E2EE to ActivityPub.",
    },
    "plurality-in-practice-case-file.md": {
        "description": "A case file imagining a future where decision-making and resource allocation are driven by nuanced voting protocols that consider voter identity and expertise, moving beyond the limitations of traditional one-person-one-vote systems.",
    },
    "shoreline-adaptations-case-file.md": {
        "description": "In a world defined by rising sea levels, can we learn to live better in wetter cities? A case file on sea level rise adaptation and how communities and engineering agencies are developing new protocols for urban water management.",
    },
}

DELETE_FILES = ["summer-of-protocols-research-steiert-1.md"]


def update_frontmatter_field(content: str, field: str, new_value: str) -> str:
    """Replace a frontmatter scalar field (description or title)."""
    # Handle multi-line values: match from field: to next non-indented line or ---
    pattern = rf'^{field}:.*'
    new_line = f'{field}: "{new_value}"'
    return re.sub(pattern, new_line, content, flags=re.MULTILINE)


def update_authors(content: str, authors: list) -> str:
    """Replace the authors block in frontmatter."""
    authors_yaml = "authors:\n" + "".join(
        f'  - name: "{a["name"]}"\n' for a in authors
    )
    # Match existing authors block (authors: through last indented line before next key)
    pattern = r'^authors:\n(?:  .*\n)+'
    return re.sub(pattern, authors_yaml, content, flags=re.MULTILINE)


changed = []
skipped = []

for filename, fix in FIXES.items():
    path = os.path.join(RESOURCES_DIR, filename)
    if not os.path.exists(path):
        skipped.append(filename)
        continue

    with open(path, "r") as f:
        content = f.read()

    original = content

    if "title" in fix:
        content = update_frontmatter_field(content, "title", fix["title"])
    if "description" in fix:
        content = update_frontmatter_field(content, "description", fix["description"])
    if "authors" in fix:
        content = update_authors(content, fix["authors"])

    if content != original:
        with open(path, "w") as f:
            f.write(content)
        changed.append(filename)
    else:
        skipped.append(f"{filename} (no change)")

# Delete duplicates
deleted = []
for filename in DELETE_FILES:
    path = os.path.join(RESOURCES_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        deleted.append(filename)

print(f"\nUpdated ({len(changed)}):")
for f in sorted(changed):
    print(f"  {f}")

if deleted:
    print(f"\nDeleted ({len(deleted)}):")
    for f in deleted:
        print(f"  {f}")

if skipped:
    print(f"\nSkipped ({len(skipped)}):")
    for f in skipped:
        print(f"  {f}")

# Print D1 update slugs for reference
print("\nSlugs needing D1 update:")
for filename in sorted(changed):
    slug = filename.replace(".md", "")
    print(f"  {slug}")
if deleted:
    print("Slugs needing D1 DELETE:")
    for filename in deleted:
        slug = filename.replace(".md", "")
        print(f"  {slug}")
