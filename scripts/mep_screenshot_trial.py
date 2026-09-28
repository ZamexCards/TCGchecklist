#!/usr/bin/env python3
"""One-card visual capture trial; only verified captures are archived."""
import asyncio,json,re
from pathlib import Path
from PIL import Image, ImageChops
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
                            # Remove only the near-white canvas outside the physical card.
                            # Keep the original rounded grey/silver printed card border.
                            background=Image.new('RGB',rgb.size,(255,255,255))
                            difference=ImageChops.difference(rgb,background).convert('L').point(lambda x: 255 if x>25 else 0)
                            bbox=difference.getbbox()
                            result['detected_card_bounds']=list(bbox) if bbox else None
                            if not bbox or bbox[2]-bbox[0]<300 or bbox[3]-bbox[1]<400:
                                result['status']='card_bounds_not_verified'
                            else:
                                cropped=rgb.crop(bbox)
                                result['cropped_dimensions']=list(cropped.size)
                                if not .62 < cropped.width/cropped.height < .82:
                                    result['status']='cropped_ratio_invalid'
                                else:
                                    cropped.save(out,format='PNG',optimize=True)
                                    result['status']='saved'
                            result['local_path']='./assets/sets/mep/001.png'
                    temp.unlink(missing_ok=True)
            await browser.close()
    except Exception as exc:
        result['status']='error_'+type(exc).__name__
        result['detail']=str(exc)[:350]
    REPORT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('MEP SCREENSHOT:',json.dumps(result),flush=True)
asyncio.run(main())
