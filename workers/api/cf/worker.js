// Public Cloudflare Analytics JSON endpoint
// GET /api/cf -> { active_viewers, daily_visitors }

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/api/cf") {
      try {
        const data = await getCloudflareCounts(env);
        return jsonResponse({
          site: env.SITE_NAME || url.host,
          active_viewers: data.active,
          daily_visitors: data.daily,
          timestamp: new Date().toISOString(),
          source: "cloudflare_analytics",
        });
      } catch (err) {
        return jsonResponse({ error: err.message }, 500);
      }
    }

    return new Response("Not found", { status: 404 });
  },
};

async function getCloudflareCounts(env) {
  const now = new Date();
  const nowISO = now.toISOString();
  const fiveMinAgo = new Date(now.getTime() - 5 * 60 * 1000).toISOString();
  const today = now.toISOString().slice(0, 10); // YYYY-MM-DD

  const query = `
    query($zoneTag: string, $from5: Time, $to: Time, $today: Date) {
      viewer {
        zones(filter: { zoneTag: $zoneTag }) {
          httpRequests1mGroups(
            filter: { datetime_geq: $from5, datetime_lt: $to }
            limit: 500
          ) {
            uniq { uniques }
          }
          httpRequests1dGroups(filter: { date_eq: $today }) {
            uniq { uniques }
          }
        }
      }
    }`;

  const variables = {
    zoneTag: env.ZONE_ID,
    from5: fiveMinAgo,
    to: nowISO,
    today,
  };

  const resp = await fetch("https://api.cloudflare.com/client/v4/graphql", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${env.CF_GQL_TOKEN}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  if (!resp.ok) throw new Error(`Cloudflare API ${resp.status}`);
  const body = await resp.json();
  if (!body?.data?.viewer?.zones?.length)
    throw new Error("No data from Cloudflare");

  const zone = body.data.viewer.zones[0];
  const oneMinGroups = zone.httpRequests1mGroups ?? [];
  const dayGroups = zone.httpRequests1dGroups ?? [];

  // Active viewers = sum of unique IPs in last 5 min
  const active = oneMinGroups.reduce(
    (sum, g) => sum + (g?.uniq?.uniques || 0),
    0
  );
  // Daily visitors = today's unique
  const daily = dayGroups[0]?.uniq?.uniques || 0;

  return { active, daily };
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json" },
  });
}
