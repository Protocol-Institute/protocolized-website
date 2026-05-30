import type { APIRoute } from "astro";
import lexiconData from "../../data/lexicon.json";

export const GET: APIRoute = () => {
  return new Response(JSON.stringify(lexiconData, null, 2), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
};
