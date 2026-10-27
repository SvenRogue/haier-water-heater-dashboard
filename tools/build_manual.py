"""Build the portable, illustrated user guide from docs/guide.md."""
from pathlib import Path
import html
import re
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'

CSS = r'''
:root{--ink:#1d1d1f;--secondary:#6e6e73;--line:#d2d2d7;--paper:#fff;--soft:#f5f5f7;--link:#0066cc;--body:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;color-scheme:light}
*{box-sizing:border-box}html{scroll-padding-top:100px}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.85;font-weight:400;-webkit-font-smoothing:antialiased}a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid var(--link);outline-offset:5px;border-radius:3px}.skip{position:absolute;left:20px;top:-80px;background:white;padding:12px;z-index:9}.skip:focus{top:8px}.topbar{position:sticky;top:0;background:#fff;z-index:2;border-bottom:1px solid #e8e8ed}.bar-inner{max-width:1160px;min-height:66px;margin:auto;padding:12px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-weight:600;color:var(--ink);font-size:19px;line-height:1.4}.bar-links{display:flex;gap:24px;align-items:center;font-size:14px}.bar-links a{min-height:36px;display:flex;align-items:center}.print{border:0;background:transparent;padding:5px 0;color:var(--link);font:inherit;cursor:pointer;min-height:36px}.layout{max-width:1160px;margin:auto;display:grid;grid-template-columns:206px minmax(0,720px);column-gap:72px;padding:54px 28px 96px}.sidebar{align-self:start;position:sticky;top:110px;font-size:14px;line-height:1.6}.nav-title{color:var(--secondary);font-size:13px;margin:0 0 15px}.toc{display:grid;gap:3px}.toc a{padding:9px 0;display:block;color:var(--ink);border-radius:3px}.toc a:hover{color:var(--link);text-decoration:none}.toc a[aria-current=true]{color:var(--link);font-weight:600}.mobile-contents{display:none}article{min-width:0}article>.edition{font-size:14px;color:var(--secondary);margin-bottom:12px}h1,h2,h3{font-weight:600;text-wrap:pretty;line-height:1.35}h1{font-size:40px;letter-spacing:-.02em;margin:0 0 24px}h2{font-size:29px;letter-spacing:-.015em;margin:62px 0 22px;scroll-margin-top:100px}h3{font-size:21px;margin:32px 0 12px;scroll-margin-top:100px}p{margin:0 0 18px;text-wrap:pretty}article>h1+p{font-size:21px;line-height:1.7;margin-bottom:20px}strong{font-weight:600}ul,ol{padding-left:1.45em;margin:18px 0 24px}li{padding-left:.25em;margin:10px 0}li p{margin:0 0 12px}blockquote{margin:26px 0;padding:18px 22px;border:0;border-radius:8px;background:var(--soft);font-size:16px;line-height:1.8}blockquote p{margin:0}code{font-family:var(--mono);font-size:.84em;overflow-wrap:anywhere;background:var(--soft);padding:.15em .3em;border-radius:3px}pre{background:var(--soft);border-radius:8px;padding:20px 22px;margin:22px 0 26px;overflow-x:auto;line-height:1.65;font-size:15px;tab-size:2}pre code{background:none;padding:0;font-size:inherit;overflow-wrap:normal;white-space:pre}table{border-collapse:collapse;width:100%;margin:24px 0 30px;font-size:15px;line-height:1.7;text-align:left}th{font-weight:600;color:var(--ink);padding:12px 12px 12px 0;border-bottom:1px solid var(--line);vertical-align:top}td{padding:15px 12px 15px 0;border-bottom:1px solid #e8e8ed;vertical-align:top}th:last-child,td:last-child{padding-right:0}table code{font-size:.83em;word-break:break-word}figure{margin:28px 0 36px;break-inside:avoid}figure svg{display:block;width:100%;height:auto}figcaption{font-size:13px;line-height:1.75;color:var(--secondary);padding-top:12px}footer{border-top:1px solid #e8e8ed;padding:25px 28px 40px;font-size:13px;line-height:1.8;color:var(--secondary)}.footer-inner{max-width:1104px;margin:auto}.footer-inner p{margin:0 0 8px}.back-top{display:inline-block;padding:10px 0;min-height:44px}
@media(max-width:1000px){.layout{grid-template-columns:180px minmax(0,1fr);gap:36px}h1{font-size:35px}}
@media(max-width:760px){html{scroll-padding-top:92px}.bar-inner{min-height:64px;padding:12px 22px}.brand{font-size:16px;max-width:180px}.bar-links{gap:16px;font-size:13px}.bar-links .repository{display:none}.layout{display:block;padding:28px 22px 64px}.sidebar{display:none}.mobile-contents{display:block;background:var(--soft);padding:12px 16px;border-radius:8px;margin-bottom:32px;font-size:15px}.mobile-contents summary{cursor:pointer;min-height:28px;line-height:28px;font-weight:600}.mobile-contents .toc{padding-top:12px}.toc a{min-height:44px}h1{font-size:32px;line-height:1.4;margin-bottom:20px}h2{font-size:25px;margin-top:48px}h3{font-size:20px}body{font-size:17px;line-height:1.85}article>h1+p{font-size:20px}pre{font-size:13px;padding:18px 16px}table{font-size:14px;table-layout:fixed}td,th{padding-right:12px}figure{margin:24px 0 30px}blockquote{padding:16px 18px}footer{padding-left:22px;padding-right:22px}}
@media print{@page{size:A4;margin:18mm 17mm 20mm}html{scroll-padding:0}body{font-size:12pt;line-height:1.7;color:#1d1d1f}.topbar,.sidebar,.mobile-contents,.skip,.back-top{display:none!important}.layout{display:block;max-width:none;padding:0;margin:0}article{max-width:none}article>.edition{font-size:12pt}h1{font-size:25pt;margin:0 0 16pt}article>h1+p{font-size:15pt}h2{font-size:18pt;margin:30pt 0 12pt;break-after:avoid}h3{font-size:14pt;margin:20pt 0 9pt;break-after:avoid}p{margin-bottom:12pt;orphans:3;widows:3}li{margin:7pt 0}blockquote{font-size:12pt;padding:12pt 14pt;break-inside:avoid}code,table code{font-size:12pt}pre{font-size:12pt;line-height:1.6;padding:12pt;white-space:pre-wrap;break-inside:avoid}pre code{white-space:pre-wrap;overflow-wrap:anywhere}table{font-size:12pt;table-layout:fixed}th:first-child,td:first-child{width:30%}th:last-child,td:last-child{width:70%}table code{font-size:11pt;overflow-wrap:anywhere}tr{break-inside:avoid}td,th{padding:9pt 8pt 9pt 0}figure{margin:20pt 0;break-inside:avoid}figure svg{max-height:145mm}figcaption{font-size:12pt}footer{padding:18pt 0 0;margin-top:28pt;font-size:12pt}a{color:inherit;text-decoration:none}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''


def main():
    source=(DOCS/'guide.md').read_text(encoding='utf-8')
    def figure(match):
        caption,path=match.groups()
        image=(DOCS/path).resolve()
        assert image.is_relative_to(DOCS.resolve()) and image.suffix=='.svg'
        svg=image.read_text(encoding='utf-8')
        return '<figure>'+svg+'<figcaption>'+html.escape(caption)+'</figcaption></figure>'
    source=re.sub(r'!\[([^\]]+)\]\(([^)]+)\)',figure,source)
    rendered=markdown.markdown(source,extensions=['tables','fenced_code','attr_list'])
    headings=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',rendered)
    toc='<nav class="toc" aria-label="本页目录">'+''.join('<a href="#'+ident+'">'+text+'</a>' for ident,text in headings)+'</nav>'
    content='''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="海尔热水器 Home Assistant 控制面板使用手册，包含安装步骤、控件图示与模式切换说明。"><title>热水器控制面板使用手册 · v1.1.0</title><style>'''+CSS+'''</style></head>
<body id="top"><a class="skip" href="#content">跳至正文</a><header class="topbar"><div class="bar-inner"><a class="brand" href="#top">热水器控制面板</a><div class="bar-links"><a class="repository" href="https://github.com/SvenRogue/haier-water-heater-dashboard">项目仓库</a><a href="https://github.com/SvenRogue/haier-water-heater-dashboard/releases/tag/v1.1.0">下载</a><button type="button" class="print" onclick="window.print()">打印</button></div></div></header>
<div class="layout"><aside class="sidebar"><p class="nav-title">使用手册</p>'''+toc+'''</aside><main id="content"><details class="mobile-contents"><summary>本页目录</summary>'''+toc+'''</details><article><p class="edition">使用手册 · v1.1.0</p>'''+rendered+'''<a class="back-top" href="#top">返回顶部 ↑</a></article></main></div>
<footer><div class="footer-inner"><p>海尔热水器控制面板 · v1.1.0 · MIT 许可</p><p>独立开源项目，与海尔、Home Assistant 及 Apple 官方无隶属关系。图示为合成演示，不包含家庭真实数据。</p></div></footer>
<script>
if ('IntersectionObserver' in window) {
 const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){document.querySelectorAll('.toc a').forEach(a=>a.setAttribute('aria-current',String(a.hash==='#'+entry.target.id)))}}},{rootMargin:'-12% 0px -65% 0px'});
 document.querySelectorAll('h2[id]').forEach(h=>observer.observe(h));
}
document.querySelectorAll('.mobile-contents a').forEach(a=>a.addEventListener('click',()=>{document.querySelector('.mobile-contents').open=false}));
</script></body></html>'''
    (DOCS/'index.html').write_text(content,encoding='utf-8')
    print('Built docs/index.html with',len(headings),'sections and two embedded illustrations')


if __name__=='__main__':
    main()
