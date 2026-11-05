// Isolated UI smoke check: no account credentials or paid generation calls.
// REEL_SMOKE_VIDEO must point to a small H264 MP4 fixture.
const fs = require('fs');
const path = require('path');
const http = require('http');
const assert = require('assert');
const babel = require('@babel/core');
const puppeteer = require('puppeteer');
const root = path.resolve(__dirname, '..');
const videoPath = process.env.REEL_SMOKE_VIDEO;
if (!videoPath) throw new Error('Set REEL_SMOKE_VIDEO to a small MP4 fixture.');
const moduleScript = (name, folder = 'Chat') => {
    const code = babel.transformSync(fs.readFileSync(path.join(root, 'src/components', folder, `${name}.js`), 'utf8'), {
        configFile: false, babelrc: false,
        presets: [require.resolve('@babel/preset-react')],
        plugins: [require.resolve('@babel/plugin-transform-modules-commonjs')],
    }).code;
    return `(function(){const module={exports:{}};const exports=module.exports;const require=(id)=>id==='react'?window.React:id==='react-dom'?window.ReactDOM:id==='./ReelPlayer'?window.ReelPlayer:id==='../Theme'?window.ThemePrimitives:id.includes('CreditsModal')?(()=>null):id.includes('toast')?{showToast:()=>{}}:{};${code};window.${name}=module.exports.default||module.exports;})();`;
};
const assets = {
    '/react.js': fs.readFileSync(path.join(path.dirname(require.resolve('react/package.json')), 'umd/react.development.js')),
    '/react-dom.js': fs.readFileSync(path.join(path.dirname(require.resolve('react-dom/package.json')), 'umd/react-dom.development.js')),
    '/player.js': moduleScript('ReelPlayer'), '/studio.js': moduleScript('ReelStudioModal'),
    '/theme.js': moduleScript('ThemePrimitives', 'Theme'),
    '/style.css': fs.readFileSync(path.join(root, 'src/components/Chat/ReelPlayer.css')),
};
const server = http.createServer((req, res) => {
    if (req.url.includes('/download')) { res.setHeader('Content-Type', 'video/mp4'); fs.createReadStream(videoPath).pipe(res); return; }
    if (assets[req.url]) { res.setHeader('Content-Type', req.url.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(assets[req.url]); return; }
    res.end('<html><head><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script src="/react.js"></script><script src="/react-dom.js"></script><script src="/theme.js"></script><script src="/player.js"></script><script src="/studio.js"></script></body></html>');
});
(async () => {
    let browser;
    try {
        await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
        browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
        const page = await browser.newPage();
        const errors = [];
        page.on('pageerror', (error) => errors.push(error.message));
        await page.goto(`http://127.0.0.1:${server.address().port}`);
        await page.evaluate(() => {
            window.calls = [];
            const realFetch = window.fetch.bind(window);
            window.fetch = (url, options) => {
                window.calls.push(String(url));
                if (String(url).includes('/saved/')) return Promise.resolve(new Response(JSON.stringify({ job: { job_id: 'job_saved', status: 'completed' } }), { status: 200 }));
                if (String(url).includes('/pricing')) return Promise.resolve(new Response(JSON.stringify({ credit_cost: 25, credits: 100 }), { status: 200 }));
                if (String(url).includes('/drafts/')) return Promise.resolve(new Response(JSON.stringify({ draft_id: 'draft_test', cost_projection: {}, storyboard: [], claims: [] }), { status: 200 }));
                return realFetch(url, options);
            };
            window.root = ReactDOM.createRoot(document.getElementById('root'));
            window.root.render(React.createElement(window.ReelStudioModal, { messageId: 42, onClose: () => {} }));
        });
        await page.waitForSelector('.reel-player');
        await page.waitForFunction(() => document.querySelector('video')?.duration > 0);
        assert.equal(await page.evaluate(() => window.calls.some((url) => url.includes('/drafts/'))), false, 'Opening saved reel must not generate a draft');
        await page.evaluate(() => document.querySelector('video').pause());
        await page.waitForFunction(() => [...document.querySelectorAll('.reel-player-actions button')].some((button) => button.textContent === 'Play'));
        await page.evaluate(() => {
            const slider = document.querySelector('input[type=range]');
            const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setter.call(slider, '1.5'); slider.dispatchEvent(new Event('input', { bubbles: true })); slider.dispatchEvent(new Event('change', { bubbles: true }));
        });
        await page.waitForFunction(() => document.querySelector('video').currentTime >= 1.4);
        await page.evaluate(() => [...document.querySelectorAll('button')].find((button) => button.textContent === 'Stop').click());
        await page.waitForFunction(() => document.querySelector('video').paused && document.querySelector('video').currentTime < 0.1);
        const actions = await page.$$eval('.reel-player-social button', (buttons) => buttons.map((button) => button.textContent));
        assert.deepEqual(actions, ['Instagram', 'Facebook', 'YouTube']);
        assert.equal(await page.$eval('.reel-player', (element) => getComputedStyle(element).position), 'fixed');
        await page.screenshot({ path: '/private/tmp/astroroshni-reel-player-smoke.png' });
        await page.evaluate(() => [...document.querySelectorAll('button')].find((button) => button.textContent === 'Recreate').click());
        await page.waitForSelector('.reel-credit-confirm');
        assert.equal(await page.evaluate(() => window.calls.some((url) => url.includes('/drafts/'))), false, 'Recreate must show credit confirmation before generation');
        await page.evaluate(() => [...document.querySelectorAll('button')].find((button) => button.textContent === 'Continue').click());
        await page.waitForFunction(() => window.calls.some((url) => url.includes('/drafts/')));
        assert.deepEqual(errors, []);
        console.log('PASS: saved reel opens with no generation; player loads, pauses, seeks, stops; social export and recreate are available.');
    } finally { if (browser) await browser.close(); await new Promise((resolve) => server.close(resolve)); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
