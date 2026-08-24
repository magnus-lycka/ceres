// No server rendering and no server routes: this builds to static files that a
// browser opens. Keeping both flags here makes that a property of the app
// rather than a convention someone has to remember.
export const ssr = false;
export const prerender = true;
