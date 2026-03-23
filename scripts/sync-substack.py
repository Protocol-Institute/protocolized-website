#!/usr/bin/env python3
"""
Sync Substack posts from the Protocolized newsletter to the resources library.

Fetches the Substack RSS feed and creates a new markdown file for each post
that doesn't already exist in src/content/resources/.

Run manually:
    python3 scripts/sync-substack.py

Or triggered automatically by the GitHub Action in .github/workflows/sync-substack.yml
"""

import feedparser
import os
import re
import html
from datetime import datetime, timezone

# Configuration
SUBSTACK_FEED_URL = "https://protocolized.summerofprotocols.com/feed"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "content", "resources")
OUTPUT_DIR = os.path.normpath(OUTPUT_DIR)


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")[:80]


def escape_yaml_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def strip_html(s: str) -> str:
    """Remove HTML tags and decode entities."""
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def truncate(s: str, max_len: int = 280) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def extract_description(entry) -> str:
    """Extract a clean description from a feed entry."""
    # Try summary first, then content
    summary = getattr(entry, "summary", "") or ""
    if summary:
        clean = strip_html(summary)
        if len(clean) > 30:
            return truncate(clean)

    # Try content
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")
        clean = strip_html(content)
        if len(clean) > 30:
            return truncate(clean)

    return "A post from the Protocolized newsletter."


def get_existing_slugs() -> set:
    """Get all existing resource slugs to avoid duplicates."""
    slugs = set()
    if not os.path.exists(OUTPUT_DIR):
        return slugs
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".md"):
            slugs.add(f[:-3])
    return slugs


def get_existing_urls() -> set:
    """Check existing markdown files for URLs to avoid adding duplicates."""
    urls = set()
    if not os.path.exists(OUTPUT_DIR):
        return urls
    for f in os.listdir(OUTPUT_DIR):
        if not f.endswith(".md"):
            continue
        filepath = os.path.join(OUTPUT_DIR, f)
        try:
            with open(filepath, "r") as fh:
                content = fh.read()
            match = re.search(r'^url:\s*"([^"]+)"', content, re.MULTILINE)
            if match:
                urls.add(match.group(1))
        except Exception:
            pass
    return urls


def infer_tags(title: str, description: str) -> list:
    """Infer relevant tags from title and description text."""
    text = (title + " " + description).lower()
    tag_keywords = {
        "governance": ["governance", "govern", "policy", "regulation"],
        "coordination": ["coordination", "coordinate", "collective"],
        "AI": ["ai", "artificial intelligence", "machine learning", "llm", "gpt"],
        "blockchain": ["blockchain", "crypto", "ethereum", "web3", "defi"],
        "memory": ["memory", "archive", "remembering"],
        "fiction": ["fiction", "story", "narrative", "speculative"],
        "climate": ["climate", "environment", "carbon", "green"],
        "infrastructure": ["infrastructure", "network", "internet", "protocol stack"],
        "community": ["community", "social", "collective", "commons"],
        "theory": ["theory", "theoretical", "framework", "concept"],
        "design": ["design", "designer", "ux", "interface"],
        "standards": ["standard", "specification", "rfc", "ieee"],
        "economics": ["economic", "market", "incentive", "money"],
    }

    found_tags = ["protocols"]
    for tag, keywords in tag_keywords.items():
        if any(kw in text for kw in keywords):
            found_tags.append(tag)
            if len(found_tags) >= 4:
                break

    return found_tags


def create_markdown(entry, slug: str) -> str:
    """Generate a markdown file from a feed entry."""
    title = escape_yaml_str(strip_html(getattr(entry, "title", "Untitled")))
    url = getattr(entry, "link", "")
    description = escape_yaml_str(extract_description(entry))

    # Parse publication date
    try:
        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        date_str = pub_date.strftime("%Y-%m-%d")
    except Exception:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Infer tags
    tags = infer_tags(title, description)

    lines = [
        "---",
        f'title: "{title}"',
        "type: article",
        "authors:",
        '  - name: "Protocolized"',
        '    url: "https://protocolized.summerofprotocols.com"',
        f"date: {date_str}",
        f'description: "{description}"',
        "tags:",
    ]
    for tag in tags:
        lines.append(f"  - {tag}")
    lines += [
        "audience:",
        "  - researcher",
        "  - practitioner",
        "featured: false",
        f'url: "{escape_yaml_str(url)}"',
        "---",
        "",
    ]

    return "\n".join(lines)


def main():
    print(f"Fetching Substack feed: {SUBSTACK_FEED_URL}")
    feed = feedparser.parse(SUBSTACK_FEED_URL)

    if feed.bozo:
        print(f"Warning: Feed parse issue: {feed.bozo_exception}")

    existing_slugs = get_existing_slugs()
    existing_urls = get_existing_urls()

    print(f"Found {len(feed.entries)} entries in feed")
    print(f"Existing resources: {len(existing_slugs)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    created = 0
    skipped = 0

    for entry in feed.entries:
        url = getattr(entry, "link", "")

        # Skip if URL already exists
        if url and url in existing_urls:
            skipped += 1
            continue

        # Generate slug from URL or title
        title = strip_html(getattr(entry, "title", "untitled"))
        # Try to extract slug from URL path
        url_match = re.search(r"/p/([^/?#]+)", url)
        if url_match:
            base_slug = slugify(url_match.group(1))
        else:
            base_slug = slugify(title)

        # Ensure unique slug
        slug = base_slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

        existing_slugs.add(slug)
        if url:
            existing_urls.add(url)

        content = create_markdown(entry, slug)
        out_path = os.path.join(OUTPUT_DIR, f"{slug}.md")

        with open(out_path, "w") as f:
            f.write(content)

        print(f"  Created: {slug}.md ({title[:50]})")
        created += 1

    print(f"\nDone. Created: {created}, Skipped (already exists): {skipped}")


if __name__ == "__main__":
    main()
