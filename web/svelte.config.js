import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    // Static output only. There is no server half of this application: the
    // rules run in the browser and persistence lives behind a local service.
    // Routes are prerendered, so `index.html` is the real home page; the SPA
    // fallback needs its own name or it overwrites it.
    adapter: adapter({ fallback: '200.html' }),
  },
};
