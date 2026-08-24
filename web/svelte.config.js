import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    // Static output only. There is no server half of this application: the
    // rules run in the browser and persistence lives behind a local service.
    adapter: adapter({ fallback: 'index.html' }),
  },
};
