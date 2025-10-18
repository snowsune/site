<script>
  import { onMount } from "svelte";

  let canvas;
  let colors = { primary: "#ff6b6b" };

  onMount(() => {
    const app = document.getElementById("moji-maker-app");
    const img = new Image();
    img.src = app.getAttribute("data-heart-url");
    img.onload = () => {
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, 256, 256);

      const data = ctx.getImageData(0, 0, 256, 256);
      for (let i = 0; i < data.data.length; i += 4) {
        if (data.data[i + 3] === 0) continue; // skip transparent
        if (data.data[i] > 100) {
          // if reddish
          const hex = colors.primary;
          data.data[i] = parseInt(hex.slice(1, 3), 16);
          data.data[i + 1] = parseInt(hex.slice(3, 5), 16);
          data.data[i + 2] = parseInt(hex.slice(5, 7), 16);
        }
      }
      ctx.putImageData(data, 0, 0);
    };
  });

  function update() {
    onMount(); // re-run on color change
  }
</script>

<canvas bind:this={canvas} width="256" height="256"></canvas>
<input type="color" bind:value={colors.primary} on:change={update} />
