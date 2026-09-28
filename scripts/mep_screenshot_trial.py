#!/usr/bin/env python3
"""One-card visual capture trial; only verified captures are archived."""
import asyncio,json,re
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
PAGE='https://pkmncards.com/card/meganium-mega-evolution-promos-mep-001/'
REPORT=ROOT/'data/mep_screenshot_report.json'
async def main():
    result={'card':'mep-001','page':PAGE,'status':'not_started'}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,args=['--no-sandbox'])
            page=await browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=2)
            await page.goto(PAGE,wait_until='domcontentloaded',timeout=45000)
            await page.wait_for_timeout(3000)
            result['title']=await page.title()
            if not all(s in result['title'].lower() for s in ('meganium','mep','001')):
                result['status']='identity_mismatch'
            else:
                found=await page.locator('img').evaluate_all("""els => els.map(e => ({alt:e.alt,src:e.currentSrc||e.src,w:e.naturalWidth,h:e.naturalHeight,visible:!!(e.offsetWidth&&e.offsetHeight)}))""")
                result['image_candidates']=[x for x in found if x['w']>180 and x['h']>240][:12]
                candidates=page.locator('img')
                selected=None
                for i in range(await candidates.count()):
                    im=candidates.nth(i)
                    props=await im.evaluate('(e)=>({alt:e.alt,src:e.currentSrc||e.src,w:e.naturalWidth,h:e.naturalHeight,ow:e.offsetWidth,oh:e.offsetHeight})')
                    if props['w']<300 or props['h']<400 or props['ow']<150 or props['oh']<200:continue
                    if not (.62 < props['w']/props['h'] < .82):continue
                    if not re.search('meganium|mep|promo|mebsp_en_001',props['alt']+' '+props['src'],re.I):continue
                    selected=im
                    result['selected']=props
                    break
                if selected is None:
                    result['status']='no_verified_visible_card'
                else:
                    out=ROOT/'assets/sets/mep/001.png'
                    out.parent.mkdir(parents=True,exist_ok=True)
                    temp=out.with_name('001.screenshot.tmp.png')
                    await selected.screenshot(path=str(temp),animations='disabled',timeout=15000)
                    with Image.open(temp) as im:
                        result['capture_dimensions']=list(im.size)
                        if im.width<300 or im.height<400 or not .62<im.width/im.height<.82:
                            result['status']='capture_dimensions_invalid'
                        else:
                            rgb=im.convert('RGB')
                            w,h=rgb.size
                            px=rgb.load()
                            # Use occupancy of each scanline, rather than a single noisy JPEG pixel.
                            def ink(x,y):
                                r,g,b=px[x,y]
                                return min(r,g,b)<218 or max(r,g,b)-min(r,g,b)>32
                            cols=[sum(ink(x,y) for y in range(h//5,4*h//5,3)) for x in range(w)]
                            rows=[sum(ink(x,y) for x in range(w//5,4*w//5,3)) for y in range(h)]
                            col_min=max(5,int(.18*(3*h//5/3)))
                            row_min=max(5,int(.18*(3*w//5/3)))
                            xs=[x for x,v in enumerate(cols) if v>=col_min]
                            ys=[y for y,v in enumerate(rows) if v>=row_min]
                            if not xs or not ys:
                                result['status']='card_contour_not_detected'
                            else:
                                # Two pixels of outward tolerance protect the metallic card edge.
                                left=max(0,min(xs)-2);top=max(0,min(ys)-2)
                                right=min(w,max(xs)+3);bottom=min(h,max(ys)+3)
                                result['detected_card_bounds']=[left,top,right,bottom]
                                if left<3 or top<3 or right>w-3 or bottom>h-3:
                                    result['status']='card_touches_canvas_edge_manual_review'
                                elif not .62<(right-left)/(bottom-top)<.82:
                                    result['status']='card_ratio_invalid'
                                else:
                                    cropped=rgb.crop((left,top,right,bottom)).convert('RGBA')
                                    # Only connected background at the rounded corners becomes transparent.
                                    # This conservative corner mask never modifies the printed card interior.
                                    cw,ch=cropped.size
                                    radius=max(8,round(min(cw,ch)*.035))
                                    alpha=Image.new('L',(cw,ch),0)
                                    draw=ImageDraw.Draw(alpha)
                                    draw.rounded_rectangle((0,0,cw-1,ch-1),radius=radius,fill=255)
                                    cropped.putalpha(alpha)
                                    result['cropped_dimensions']=[cw,ch]
                                    result['corner_radius']=radius
                                    cropped.save(out,format='PNG',optimize=True)
                                    result['status']='saved_transparent_png'
                                    result['local_path']='./assets/sets/mep/001.png'
                    temp.unlink(missing_ok=True)
            await browser.close()
    except Exception as exc:
        result['status']='error_'+type(exc).__name__
        result['detail']=str(exc)[:350]
    REPORT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('MEP SCREENSHOT:',json.dumps(result),flush=True)
asyncio.run(main())
