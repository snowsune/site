import { createBracket } from "https://cdn.jsdelivr.net/npm/bracketry@1.1.3/+esm";

const dataEl = document.getElementById("bracket-data");
const wrapper = document.getElementById("rumble-bracket");

if (dataEl && wrapper) {
  const data = JSON.parse(dataEl.textContent);

  if (data.rounds && data.rounds.length) {
    const css = getComputedStyle(document.documentElement);
    const text = css.getPropertyValue("--text-color").trim() || "#000";
    const tile = css.getPropertyValue("--tile-background").trim() || "#fff";
    const border = css.getPropertyValue("--border-color").trim() || "#ccc";
    const accent = css.getPropertyValue("--accent-color").trim() || "#00bcd4";
    const sidebar = css.getPropertyValue("--sidebar-bg").trim() || "#eee";

    const pfpSize = 44;

    createBracket(data, wrapper, {
      width: "100%",
      // No height = expand to full bracket content
      useClassicalLayout: true,
      visibleRoundsCount: 0,
      navButtonsPosition: "hidden",
      showScrollbar: false,
      verticalScrollMode: "native",
      roundTitlesFontSize: 0,
      roundTitlesVerticalPadding: 0,
      rootBgColor: tile,
      rootBorderColor: "transparent",
      wrapperBorderColor: "transparent",
      roundTitlesBorderColor: "transparent",
      roundTitleColor: text,
      matchTextColor: text,
      connectionLinesColor: border,
      highlightedConnectionLinesColor: accent,
      hoveredMatchBorderColor: accent,
      liveMatchBorderColor: accent,
      liveMatchBgColor: sidebar,
      matchStatusBgColor: accent,
      matchMinVerticalGap: 20,
      onMatchSideClick(match, sideIndex) {
        const side = match.sides && match.sides[sideIndex];
        if (!side || !side.contestantId) return;
        const entry = data.contestants && data.contestants[side.contestantId];
        if (entry && entry.profileUrl) {
          window.location.href = entry.profileUrl;
        }
      },
      getRoundTitleElement() {
        const el = document.createElement("div");
        el.style.cssText = "height:0;overflow:hidden;padding:0;margin:0;";
        return el;
      },
      getNationalityHTML(player) {
        if (!player.nationality) {
          return (
            `<span style="display:inline-block;width:${pfpSize}px;` +
            `height:${pfpSize}px;border-radius:50%;background:${sidebar};` +
            `border:1px solid ${border};vertical-align:middle;"></span>`
          );
        }
        return (
          `<img src="${player.nationality}" alt="" width="${pfpSize}" height="${pfpSize}" ` +
          `style="width:${pfpSize}px;height:${pfpSize}px;border-radius:50%;` +
          `object-fit:cover;vertical-align:middle;border:1px solid ${border};">`
        );
      },
    });
  }
}
