import {readFileSync, existsSync, readdirSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../public');
const htmlFiles = readdirSync(root).filter(p => p.endsWith('.html'));
for (const file of htmlFiles) {
 const html = readFileSync(resolve(root, file), 'utf8');
 assert.match(html, /<html lang="zh-CN">/);
 assert.match(html, /name="viewport"/);
 for (const [,url] of html.matchAll(/(?:href|src)="([^"#]+)"/g)) {
  if (!url.startsWith('/') || url === '/') continue;
  assert.ok(existsSync(resolve(root, '.' + url.split('#')[0])), `${file}: missing ${url}`);
 }
 for (const [,id] of html.matchAll(/href="#([^"]+)"/g)) assert.ok(html.includes(`id="${id}"`), `${file}: missing anchor ${id}`);
}
const home=readFileSync(resolve(root,'index.html'),'utf8');
assert.equal((home.match(/<h1\b/g)||[]).length,1);
assert.ok(home.includes('id6800402462'));
assert.ok(home.includes('非 App 界面或检测结果'));
assert.ok(home.includes('3 个单视频'));
assert.ok(home.includes('不识别身份'));
assert.ok(!/<form|type="file"|https?:\/\/[^" ]+\.js/.test(home));
console.log(`PASS: ${htmlFiles.length} HTML pages; local links, anchors, store ID, capability boundaries, no upload/tracker.`);
