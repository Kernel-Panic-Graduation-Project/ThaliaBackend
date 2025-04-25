CONFIG_MODEL_CATEGORY = ['Disney Princess', 'Sousou no Frieren']

CONFIG_CHECKPOINT = {
  'Disney Princess'   : 'realcartoonXL_v7',
  'Sousou no Frieren' : 'aamXLAnimeMix_v10',
}

CONFIG_LORA = {
  'Disney Princess'   : '<lora:add-detail-xl:1> <lora:princess_xl_v2:0.8>',
  'Sousou no Frieren' : '<lora:frieren_nereirfpnxl_xl:1>',
}

CONFIG_PROMPT = {
  'Disney Princess'   : '',
  'Sousou no Frieren' : 'nereirfpnxl, frieren, 1girl, pointy ears, staff, elf, earrings, scarf, jewelry, twintails, green eyes, long hair, best quality, intricate detail, cinematic lighting, amazing quality, amazing shading, detailed Illustration',
}

CONFIG_NEGATIVE_PROMPT = {
  'Disney Princess'   : 'easynegative, badhandv4, (low quality, worst quality:1.4), deformed, censored, bad anatomy, watermark, signature, nsfw,explicit',
  'Sousou no Frieren' : 'easynegative, badhandv4, (low quality, worst quality:1.4), deformed, censored, bad anatomy, watermark, signature, nsfw,explicit',
}

CONFIG_SAMPLER = {
  'Disney Princess'   : 'DPM++ 2M Karras',
  'Sousou no Frieren' : 'Euler a',
}

CONFIG_UPSCALER = {
  'Disney Princess'   : 'R-ESRGAN 4x+',
  'Sousou no Frieren' : 'Latent',
}

CONFIG_WIDTH = {
  'Disney Princess'   : 960,
  'Sousou no Frieren' : 960,
}

CONFIG_HEIGHT = {
  'Disney Princess'   : 540,
  'Sousou no Frieren' : 540,
}

CONFIG_GUIDANCE_SCALE = {
  'Disney Princess'   : 10.0,
  'Sousou no Frieren' : 5.0,
}

CONFIG_STEPS = {
  'Disney Princess'   : 35,
  'Sousou no Frieren' : 25,
}

CONFIG_SEED = {
  'Disney Princess'   : -1,
  'Sousou no Frieren' :  772023831,
}

CONFIG_DENOISING_STRENGTH = {
  'Disney Princess'   : 0.45,
  'Sousou no Frieren' : 0.45,
}

CONFIG_UPSCALE_FACTOR  = {
  'Disney Princess'   : 2,
  'Sousou no Frieren' : 2,
}
