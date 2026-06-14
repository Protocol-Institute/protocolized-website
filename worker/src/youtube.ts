const CHANNEL_ID = "UCcNZ6wTbeeAJ-O_OIhs2j3A";
const FEED_URL = `https://www.youtube.com/feeds/videos.xml?channel_id=${CHANNEL_ID}`;

export interface YouTubeVideo {
  videoId: string;
  title: string;
  url: string;
  thumbnail: string;
  published: string;
  description: string;
}

function parseEntry(entry: string): YouTubeVideo | null {
  const videoId = (entry.match(/<yt:videoId>(.*?)<\/yt:videoId>/) ?? [])[1];
  if (!videoId) return null;
  const rawTitle = (entry.match(/<title>(.*?)<\/title>/) ?? [])[1] ?? "";
  const published = (entry.match(/<published>(.*?)<\/published>/) ?? [])[1] ?? "";
  const rawDesc = (entry.match(/<media:description>([\s\S]*?)<\/media:description>/) ?? [])[1] ?? "";
  const unescape = (s: string) =>
    s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"');
  return {
    videoId,
    title: unescape(rawTitle),
    url: `https://www.youtube.com/watch?v=${videoId}`,
    thumbnail: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
    published: published.slice(0, 10),
    description: unescape(rawDesc).trim().slice(0, 200),
  };
}

export async function getLatestYouTubeVideos(limit = 2): Promise<YouTubeVideo[]> {
  try {
    const res = await fetch(FEED_URL, {
      // Cloudflare edge-caches the RSS response for 1 hour
      cf: { cacheTtl: 3600, cacheEverything: true },
    } as RequestInit);
    if (!res.ok) return [];
    const xml = await res.text();
    return xml
      .split("<entry>")
      .slice(1)
      .map(parseEntry)
      .filter((v): v is YouTubeVideo => v !== null)
      .slice(0, limit);
  } catch {
    return [];
  }
}
