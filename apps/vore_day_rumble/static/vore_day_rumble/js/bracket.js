import { createBracket } from "https://cdn.jsdelivr.net/npm/bracketry@1.1.3/+esm";

const dataEl = document.getElementById("bracket-data");
const wrapper = document.getElementById("rumble-bracket");

if (dataEl && wrapper) {
  const data = JSON.parse(dataEl.textContent);

  if (data.rounds && data.rounds.length) {
    const round1Count = (data.matches || []).filter((m) => m.roundIndex === 0)
      .length;
    const height = Math.max(420, round1Count * 88);

    createBracket(data, wrapper, {
      height: `${height}px`,
      getNationalityHTML(player) {
        if (!player.nationality) {
          return '<span style="display:inline-block;width:28px;height:28px;"></span>';
        }
        return (
          `<img src="${player.nationality}" alt="" width="28" height="28" ` +
          `style="width:28px;height:28px;border-radius:50%;object-fit:cover;` +
          `vertical-align:middle;">`
        );
      },
    });
  }
}
