"""Preview the host's real quota mask using simulated percentages."""
import colorsys
from pathlib import Path
import c100_codex_meter as meter

panels=[]
for remaining in [80,40,10]:
    colors=meter.colors_for_remaining(remaining,(0,200,255),180)
    cells=[]
    for position in range(100):
        row,col=divmod(position,10)
        on=colors[meter.physical_to_driver_index(position)][2]>0
        hue=(32+col*13+row*6)%256
        rgb=colorsys.hsv_to_rgb(hue/255,1,205/255 if on else 28/255)
        color='#'+''.join(f'{round(c*255):02x}' for c in rgb)
        cells.append(f'<i class="{"on" if on else "dim"}" style="--led:{color}"></i>')
    assert sum(c[2]>0 for c in colors)==remaining
    panels.append(f'<section><div class="number">{remaining}<small>%</small></div><p>剩余额度 · {remaining} 颗高亮灯</p><div class="matrix">'+''.join(cells)+'</div></section>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>C100 Codex 用量灯 · 模拟预览</title><style>
*{box-sizing:border-box}body{margin:0;background:#101419;color:#edf2f5;font:15px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;padding:55px}main{max-width:1250px;margin:auto}header small{color:#72bcb5;letter-spacing:4px}h1{font-size:35px;margin:16px 0 10px}header p{color:#9cabb9;margin:0 0 35px}.panels{display:grid;grid-template-columns:repeat(3,1fr);gap:23px}section{padding:28px;border:1px solid #293441;border-radius:18px;background:#19212a}.number{font-size:53px;font-weight:600;letter-spacing:-2px}.number small{font-size:21px;color:#8fa4b6;letter-spacing:0;margin-left:7px}section p{color:#a4b4c4;font-size:13px;margin:6px 0 24px}.matrix{display:grid;grid-template-columns:repeat(10,1fr);gap:6px;padding:15px;background:#090d12;border:1px solid #2a333d;border-radius:11px}i{display:block;aspect-ratio:1;background:var(--led);border-radius:3px}.on{box-shadow:0 0 9px color-mix(in srgb,var(--led) 45%,transparent);border:1px solid #ffffff30}.dim{border:1px solid #ffffff0a}footer{margin-top:28px;font-size:12px;color:#74899d;line-height:1.8}
</style><main><header><small>C100 · CODEX USAGE METER</small><h1>把剩余用量，变成桌面上的光。</h1><p>100 颗灯对应 100%，固定的灯位顺序，让每一格变化都看得见。</p></header><div class="panels">'''+''.join(panels)+'''</div><footer>模拟剩余用量 · 高亮掩码直接调用 c100_codex_meter.colors_for_remaining<br>颜色按固件的斜向 RGB 流水公式绘制为固定帧；实机上背景持续流动。</footer></main></html>'''
Path(__file__).with_name('preview.html').write_text(page,encoding='utf-8')
print('Generated preview.html')
